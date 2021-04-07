# coding: utf-8
##############################################################################

###############################################################################
import time

from odoo import fields, models, api, exceptions, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from datetime import datetime, date, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from io import BytesIO
import xlwt, base64

class FiscalBookWizard(models.TransientModel):
    _inherit = "fiscal.book.wizard"
    state = fields.Selection([('choose', 'choose'), ('get', 'get')], default='choose')
    report = fields.Binary('Descargar xls', filters='.xls', readonly=True)
    name = fields.Char('File Name', size=32)
    
    
    
    def generar_excel(self):
        if self.type == 'purchase':
            if self.date_start and self.date_end:
                fecha_inicio = self.date_start
                fecha_fin = self.date_end
                book_id = self.env.context['active_id']

                purchase_book_obj = self.env['account.move']
                purchase_book_ids = purchase_book_obj.search(
                    [('invoice_date', '>=', fecha_inicio), ('invoice_date', '<=', fecha_fin)])
                if purchase_book_ids:
                    return self.xls_compra()
                else:
                    raise ValidationError('Advertencia! No existen facturas entre las fechas seleccionadas')
        else:
            if self.date_start and self.date_end:
                fecha_inicio = self.date_start
                fecha_fin = self.date_end
                book_id = self.env.context['active_id']
                # tabla_report_z = self.env['datos.zeta.diario']
                # domain = ['|',
                #           ('fecha_ultimo_reporte_z', '>=', fecha_inicio),
                #           ('fecha_ultimo_reporte_z', '<=', fecha_fin),
                #           ('numero_ultimo_reporte_z', '>', '0')
                #           ]
                #
                # report_z_ids = tabla_report_z.search(domain, order='fecha_ultimo_reporte_z asc')
                #
                # if report_z_ids:
                #     ids = []
                #     for id in report_z_ids:
                #         ids.append(id.id)
                purchase_book_obj = self.env['account.move']
                purchase_book_ids = purchase_book_obj.search(
                    [('invoice_date', '>=', fecha_inicio), ('invoice_date', '<=', fecha_fin)])
                if purchase_book_ids:
                    return self.xls_ventas()
                else:
                    raise ValidationError('Advertencia! No existen facturas entre las fechas seleccionadas')
        return

    @api.model
    def xls_compra(self):
        format_new = "%d/%m/%Y"
        date_start = datetime.strptime(str(self.date_start), DATE_FORMAT)
        date_end = datetime.strptime(str(self.date_end), DATE_FORMAT)
        datos_compras = []
        purchasebook_ids = self.env['fiscal.book.line'].search(
            [('fb_id', '=', self.env.context['active_id']), ('accounting_date', '>=', date_start.strftime(DATETIME_FORMAT)),
             ('accounting_date', '<=', date_end.strftime(DATETIME_FORMAT))], order='emission_date asc')
        emission_date = ' '
        sum_compras_credit = 0
        sum_total_with_iva = 0
        sum_vat_general_base = 0
        sum_vat_general_tax = 0
        sum_vat_reduced_base = 0
        sum_vat_reduced_tax = 0
        sum_vat_additional_base = 0
        sum_vat_additional_tax = 0
        sum_get_wh_vat = 0
        suma_vat_exempt = 0

        vat_reduced_base = 0
        vat_reduced_rate = 0
        vat_reduced_tax = 0
        vat_additional_base = 0
        vat_additional_rate = 0
        vat_additional_tax = 0

        ''' COMPRAS DE IMPORTACIONES'''

        sum_total_with_iva_importaciones = 0
        sum_vat_general_base_importaciones = 0
        suma_base_general_importaciones = 0
        sum_base_general_tax_importaciones = 0
        sum_vat_general_tax_importaciones = 0
        sum_vat_reduced_base_importaciones = 0
        sum_vat_reduced_tax_importaciones = 0
        sum_vat_additional_base_importaciones = 0
        sum_vat_additional_tax_importaciones = 0

        hola = 0
        #######################################
        compras_credit = 0
        origin = 0
        number = 0

        for h in purchasebook_ids:
            h_vat_general_base = 0.0
            h_vat_general_rate = 0.0
            h_vat_general_tax = 0.0
            vat_general_base_importaciones = 0
            vat_general_rate_importaciones = 0
            vat_general_general_rate_importaciones = 0
            vat_general_tax_importaciones = 0
            vat_reduced_base_importaciones = 0
            vat_reduced_rate_importaciones = 0
            vat_reduced_tax_importaciones = 0
            vat_additional_tax_importaciones = 0
            vat_additional_rate_importaciones = 0
            vat_additional_base_importaciones = 0
            vat_reduced_base = 0
            vat_reduced_rate = 0
            vat_reduced_tax = 0
            vat_additional_base = 0
            vat_additional_rate = 0
            vat_additional_tax = 0
            get_wh_vat = 0

            if h.type == 'ntp':
                compras_credit = h.invoice_id.amount_untaxed

            if h.doc_type == 'N/DB':
                origin = h.affected_invoice
                if h.invoice_id:
                    if h.invoice_id.nro_ctrl:
                        busq1 = self.env['account.move'].search([('nro_ctrl', '=', h.invoice_id.nro_ctrl)])
                        if busq1:
                            for busq2 in busq1:
                                if busq2.type == 'in_invoice':
                                    number = busq2.name or ''

            sum_compras_credit += compras_credit
            suma_vat_exempt += h.vat_exempt
            planilla = ''
            expediente = ''
            total = 0
            partner = self.env['res.partner'].search([('name', '=', h.partner_name)])
            if (partner.company_type == 'company' or partner.company_type == 'person') and (
                    partner.people_type_company or partner.people_type_individual) and (
                    partner.people_type_company == 'pjdo' or partner.people_type_individual == 'pnre' or partner.people_type_individual == 'pnnr'):
                '####################### NO ES PROVEDOR INTERNACIONAL########################################################3'
                if h.invoice_id:
                    tasa = 1
                    if h.invoice_id.currency_id.name == "USD":
                        tasa = self.obtener_tasa(h.invoice_id)
                    if h.doc_type == 'N/CR':
                        total = (h.invoice_id.amount_total) * -1 * tasa
                    else:
                        total = (h.invoice_id.amount_total) * tasa
                    sum_vat_reduced_base += h.vat_reduced_base  # Base Imponible de alicuota Reducida
                    sum_vat_reduced_tax += h.vat_reduced_tax  # Impuesto de IVA alicuota reducida
                    sum_vat_additional_base += h.vat_additional_base  # BASE IMPONIBLE ALICUOTA ADICIONAL

                    sum_vat_additional_tax += h.vat_additional_tax  # IMPUESTO DE IVA ALICUOTA ADICIONAL

                    sum_total_with_iva = h.fb_id.base_amount + h.fb_id.tax_amount  # Total monto con IVA

                    # Total monto con IVA
                    sum_vat_general_base += h.vat_general_base  # Base Imponible Alicuota general
                    sum_vat_general_tax += h.vat_general_tax  # Impuesto de IVA
                    h_vat_general_base = h.vat_general_base
                    h_vat_general_rate = (
                                h.vat_general_base and h.vat_general_tax * 100 / h.vat_general_base) if h.vat_general_base else 0.0
                    h_vat_general_rate = round(h_vat_general_rate, 0)
                    h_vat_general_tax = h.vat_general_tax if h.vat_general_tax else 0.0
                    vat_reduced_base = h.vat_reduced_base
                    vat_reduced_rate = int(h.vat_reduced_base and h.vat_reduced_tax * 100 / h.vat_reduced_base)
                    vat_reduced_tax = h.vat_reduced_tax
                    vat_additional_base = h.vat_additional_base
                    vat_additional_rate = int(
                        h.vat_additional_base and h.vat_additional_tax * 100 / h.vat_additional_base)
                    vat_additional_tax = h.vat_additional_tax
                    get_wh_vat = h.get_wh_vat

                    emission_date = datetime.strftime(
                        datetime.strptime(str(h.emission_date), DEFAULT_SERVER_DATE_FORMAT),
                        format_new)
                if h.iwdl_id.invoice_id:
                    tasa = 1
                    if h.iwdl_id.invoice_id.currency_id.name == "USD":
                        tasa = self.obtener_tasa(h.iwdl_id.invoice_id)
                    if h.doc_type == 'N/CR':
                        total = (h.iwdl_id.invoice_id.amount_total) * -1 * tasa
                    else:
                        total = (h.iwdl_id.invoice_id.amount_total) * tasa
                    sum_vat_reduced_base += h.vat_reduced_base  # Base Imponible de alicuota Reducida
                    sum_vat_reduced_tax += h.vat_reduced_tax
                    # Impuesto de IVA alicuota reducida

                    sum_vat_additional_base += h.vat_additional_base  # BASE IMPONIBLE ALICUOTA ADICIONAL

                    sum_vat_additional_tax += h.vat_additional_tax  # IMPUESTO DE IVA ALICUOTA ADICIONAL

                    sum_total_with_iva = h.fb_id.base_amount + h.fb_id.tax_amount  # Total monto con IVA

                    sum_vat_general_base += h.vat_general_base  # Base Imponible Alicuota general
                    sum_vat_general_tax += h.vat_general_tax  # Impuesto de IVA
                    h_vat_general_base = h.vat_general_base
                    h_vat_general_rate = (
                                h.vat_general_base and h.vat_general_tax * 100 / h.vat_general_base) if h.vat_general_base else 0.0
                    h_vat_general_rate = round(h_vat_general_rate, 0)
                    h_vat_general_tax = h.vat_general_tax if h.vat_general_tax else 0.0
                    vat_reduced_base = h.vat_reduced_base
                    vat_reduced_rate = int(h.vat_reduced_base and h.vat_reduced_tax * 100 / h.vat_reduced_base)
                    vat_reduced_tax = h.vat_reduced_tax
                    vat_additional_base = h.vat_additional_base
                    vat_additional_rate = int(
                        h.vat_additional_base and h.vat_additional_tax * 100 / h.vat_additional_base)
                    vat_additional_tax = h.vat_additional_tax
                    get_wh_vat = h.get_wh_vat

                    emission_date = datetime.strftime(
                        datetime.strptime(str(h.emission_date), DEFAULT_SERVER_DATE_FORMAT),
                        format_new)

            if (partner.company_type == 'company' or partner.company_type == 'person') and (
                    partner.people_type_company or partner.people_type_individual) and partner.people_type_company == 'pjnd':
                '############## ES UN PROVEEDOR INTERNACIONAL ##############################################'

                if h.invoice_id:
                    tasa = 1
                    if h.invoice_id.currency_id.name == "USD":
                        tasa = self.obtener_tasa(h.invoice_id)
                    if h.invoice_id.fecha_importacion:
                        date_impor = h.invoice_id.fecha_importacion
                        emission_date = datetime.strftime(
                            datetime.strptime(str(date_impor), DEFAULT_SERVER_DATE_FORMAT),
                            format_new)
                        total = h.invoice_id.amount_total * tasa
                    else:
                        date_impor = h.invoice_id.invoice_date
                        emission_date = datetime.strftime(
                            datetime.strptime(str(date_impor), DEFAULT_SERVER_DATE_FORMAT),
                            format_new)

                    planilla = h.invoice_id.nro_planilla_impor
                    expediente = h.invoice_id.nro_expediente_impor




                else:
                    date_impor = h.iwdl_id.invoice_id.fecha_importacion
                    emission_date = datetime.strftime(datetime.strptime(str(date_impor), DEFAULT_SERVER_DATE_FORMAT),
                                                      format_new)
                    planilla = h.iwdl_id.invoice_id.nro_planilla_impor
                    expediente = h.iwdl_id.invoice_id.nro_expediente_impor
                    tasa = 1
                    if h.iwdl_id.invoice_id.currency_id.name == "USD":
                        tasa = self.obtener_tasa(h.iwdl_id.invoice_id)
                    total = h.iwdl_id.invoice_id.amount_total * tasa
                get_wh_vat = 0.0
                vat_reduced_base = 0
                vat_reduced_rate = 0
                vat_reduced_tax = 0
                vat_additional_base = 0
                vat_additional_rate = 0
                vat_additional_tax = 0
                'ALICUOTA GENERAL IMPORTACIONES'
                vat_general_base_importaciones = h.vat_general_base
                vat_general_rate_importaciones = (h.vat_general_base and h.vat_general_tax * 100 / h.vat_general_base)
                vat_general_rate_importaciones = round(vat_general_rate_importaciones, 0)
                vat_general_tax_importaciones = h.vat_general_tax
                'ALICUOTA REDUCIDA IMPORTACIONES'
                vat_reduced_base_importaciones = h.vat_reduced_base
                vat_reduced_rate_importaciones = int(
                    h.vat_reduced_base and h.vat_reduced_tax * 100 / h.vat_reduced_base)
                vat_reduced_tax_importaciones = h.vat_reduced_tax
                'ALICUOTA ADICIONAL IMPORTACIONES'
                vat_additional_base_importaciones = h.vat_additional_base
                vat_additional_rate_importaciones = int(
                    h.vat_additional_base and h.vat_additional_tax * 100 / h.vat_additional_base)
                vat_additional_tax_importaciones = h.vat_additional_tax
                'Suma total compras con IVA'
                sum_total_with_iva = h.fb_id.base_amount + h.fb_id.tax_amount
                # Total monto con IVA
                'SUMA TOTAL DE TODAS LAS ALICUOTAS PARA LAS IMPORTACIONES'
                sum_vat_general_base_importaciones += h.vat_general_base + h.vat_reduced_base + h.vat_additional_base  # Base Imponible Alicuota general
                sum_vat_general_tax_importaciones += h.vat_general_tax + h.vat_additional_tax + h.vat_reduced_tax  # Impuesto de IVA

                'Suma total de Alicuota General'
                suma_base_general_importaciones += h.vat_general_base
                sum_base_general_tax_importaciones += h.vat_general_tax

                ' Suma total de Alicuota Reducida'
                sum_vat_reduced_base_importaciones += h.vat_reduced_base  # Base Imponible de alicuota Reducida
                sum_vat_reduced_tax_importaciones += h.vat_reduced_tax  # Impuesto de IVA alicuota reducida
                'Suma total de Alicuota Adicional'
                sum_vat_additional_base_importaciones += h.vat_additional_base  # BASE IMPONIBLE ALICUOTA ADICIONAL
                sum_vat_additional_tax_importaciones += h.vat_additional_tax  # IMPUESTO DE IVA ALICUOTA ADICIONAL

                get_wh_vat = h.get_wh_vat
            sum_get_wh_vat += h.get_wh_vat  # IVA RETENIDO

            if h_vat_general_base != 0:
                valor_base_imponible = h.vat_general_base
                valor_alic_general = h_vat_general_rate
                valor_iva = h_vat_general_tax
            else:
                valor_base_imponible = 0
                valor_alic_general = 0
                valor_iva = 0

            if get_wh_vat != 0:
                hola = get_wh_vat
            else:
                hola = 0

            if h.vat_exempt != 0:
                vat_exempt = h.vat_exempt

            else:
                vat_exempt = 0

            'Para las diferentes alicuotas que pueda tener el proveedor  internacional'
            'todas son mayor a 0'
            if vat_general_rate_importaciones > 0 and vat_reduced_rate_importaciones > 0 and vat_additional_rate_importaciones > 0:
                vat_general_general_rate_importaciones = str(vat_general_rate_importaciones) + ',' + ' ' + str(
                    vat_reduced_rate_importaciones) + ',' + ' ' + str(vat_additional_rate_importaciones) + ' '
            'todas son cero'
            if vat_general_rate_importaciones == 0 and vat_reduced_rate_importaciones == 0 and vat_additional_rate_importaciones == 0:
                vat_general_general_rate_importaciones = 0
            'Existe reducida y adicional'
            if vat_general_rate_importaciones == 0 and vat_reduced_rate_importaciones > 0 and vat_additional_rate_importaciones > 0:
                vat_general_general_rate_importaciones = str(vat_reduced_rate_importaciones) + ',' + ' ' + str(
                    vat_additional_rate_importaciones) + ' '
            'Existe general y adicional'
            if vat_general_rate_importaciones > 0 and vat_reduced_rate_importaciones == 0 and vat_additional_rate_importaciones > 0:
                vat_general_general_rate_importaciones = str(vat_general_rate_importaciones) + ',' + ' ' + str(
                    vat_additional_rate_importaciones) + ' '
            'Existe general y reducida'
            if vat_general_rate_importaciones > 0 and vat_reduced_rate_importaciones > 0 and vat_additional_rate_importaciones == 0:
                vat_general_general_rate_importaciones = str(vat_general_rate_importaciones) + ',' + ' ' + str(
                    vat_reduced_rate_importaciones) + ' '
            'Existe solo la general'
            if vat_general_rate_importaciones > 0 and vat_reduced_rate_importaciones == 0 and vat_additional_rate_importaciones == 0:
                vat_general_general_rate_importaciones = str(vat_general_rate_importaciones)
            'Existe solo la reducida'
            if vat_general_rate_importaciones == 0 and vat_reduced_rate_importaciones > 0 and vat_additional_rate_importaciones == 0:
                vat_general_general_rate_importaciones = str(vat_reduced_rate_importaciones)
            'Existe solo la adicional'
            if vat_general_rate_importaciones == 0 and vat_reduced_rate_importaciones == 0 and vat_additional_rate_importaciones > 0:
                vat_general_general_rate_importaciones = str(vat_additional_rate_importaciones)

            datos_compras.append({

                'emission_date': emission_date if emission_date else ' ',
                'partner_vat': h.partner_vat if h.partner_vat else ' ',
                'partner_name': h.partner_name,
                'people_type': h.people_type,
                'wh_number': h.wh_number if h.wh_number else ' ',
                'invoice_number': h.invoice_number,
                'affected_invoice': h.affected_invoice,
                'ctrl_number': h.ctrl_number,
                'debit_affected': h.affected_invoice,
                'credit_affected': h.affected_invoice,  # h.credit_affected,
                'type': h.void_form,
                'doc_type': h.doc_type,
                'origin': origin,
                'number': number,
                'total_with_iva': h.total_with_iva,
                'vat_exempt': vat_exempt,
                'compras_credit': compras_credit,
                'vat_general_base': valor_base_imponible,
                'vat_general_rate': valor_alic_general,
                'vat_general_tax': valor_iva,
                'vat_reduced_base': vat_reduced_base,
                'vat_reduced_rate': vat_reduced_rate,
                'vat_reduced_tax': vat_reduced_tax,
                'vat_additional_base': vat_additional_base,
                'vat_additional_rate': vat_additional_rate,
                'vat_additional_tax': vat_additional_tax,
                'get_wh_vat': hola,
                'vat_general_base_importaciones': vat_general_base_importaciones + vat_additional_base_importaciones + vat_reduced_base_importaciones,
                'vat_general_rate_importaciones': vat_general_general_rate_importaciones,
                'vat_general_tax_importaciones': vat_general_tax_importaciones + vat_reduced_tax_importaciones + vat_additional_tax_importaciones,
                'nro_planilla': planilla,
                'nro_expediente': expediente,
            })
        'SUMA TOTAL DE ALICUOTA ADICIONAL BASE'
        if sum_vat_additional_base != 0 and sum_vat_additional_base_importaciones > 0:
            sum_ali_gene_addi = sum_vat_additional_base
            sum_vat_additional_base = sum_vat_additional_base
        else:
            sum_ali_gene_addi = sum_vat_additional_base
        'SUMA TOTAL DE ALICUOTA ADICIONAL TAX'
        if sum_vat_additional_tax != 0 and sum_vat_additional_tax_importaciones > 0:
            sum_ali_gene_addi_credit = sum_vat_additional_tax
            sum_vat_additional_tax = sum_vat_additional_tax
        else:
            sum_ali_gene_addi_credit = sum_vat_additional_tax
        'SUMA TOTAL DE ALICUOTA GENERAL BASE'
        if sum_vat_general_base != 0 and suma_base_general_importaciones > 0:
            sum_vat_general_base = sum_vat_general_base
            sum_vat_general_tax = sum_vat_general_tax
        'SUMA TOTAL DE ALICUOTA REDUCIDA BASE'
        if sum_vat_reduced_base != 0 and sum_vat_reduced_base_importaciones > 0:
            sum_vat_reduced_base = sum_vat_reduced_base
            sum_vat_reduced_tax = sum_vat_reduced_tax

        ' IMPORTACIONES ALICUOTA GENERAL + ALICUOTA ADICIONAL'
        if sum_vat_additional_base_importaciones != 0:
            sum_ali_gene_addi_importaciones = sum_vat_additional_base_importaciones
        else:
            sum_ali_gene_addi_importaciones = sum_vat_additional_base_importaciones

        if sum_vat_additional_tax_importaciones != 0:
            sum_ali_gene_addi_credit_importaciones = sum_vat_additional_tax_importaciones
        else:
            sum_ali_gene_addi_credit_importaciones = sum_vat_additional_tax_importaciones

        total_compras_base_imponible = sum_vat_general_base + sum_ali_gene_addi + sum_vat_reduced_base + suma_base_general_importaciones + sum_ali_gene_addi_importaciones + sum_vat_reduced_base_importaciones + suma_vat_exempt
        total_compras_credit_fiscal = sum_vat_general_tax + sum_ali_gene_addi_credit + sum_vat_reduced_tax + sum_base_general_tax_importaciones + sum_ali_gene_addi_credit_importaciones + sum_vat_reduced_tax_importaciones

        #///////////////////////////////////////GENERANDO EXCEL////////////////////////////////////////////////////////
        fp = BytesIO()
        wb = xlwt.Workbook(encoding='utf-8')
        writer = wb.add_sheet('Nombre de hoja')
        xlwt.add_palette_colour("custom_colour", 0x21)
        wb.set_colour_RGB(0x21, 164,164,164)
        header_content_style = xlwt.easyxf("font: name Helvetica size 40 px, bold 1, height 200; align: horiz center;")
        header_content_style_left = xlwt.easyxf("font: name Helvetica size 40 px, bold 1, height 200; align: horiz left;")
        sub_header_style_1 = xlwt.easyxf(
            "font: name Helvetica size 10 px, bold 1, height 170; borders: left thin, right thin, top thin, bottom thin; align: horiz center;")
        sub_header_style = xlwt.easyxf(
            "font: name Helvetica size 10 px, bold 1, height 170; borders: left thin, right thin, top thin, bottom thin; align: horiz center; pattern: pattern solid,fore_colour custom_colour;")  # color pattern: pattern solid,fore_colour blue;
        sub_header_style_2 = xlwt.easyxf(
            "font: name Helvetica size 10 px, bold 1, height 170; borders: left thin, right thin, top thin, bottom thin; align: horiz left;")

        line_content_style_totales = xlwt.easyxf(
            "font: name Helvetica size 10 px, bold 1, height 170; borders: left thin, right thin, top thin, bottom thin; align: horiz right;",
            num_format_str='#,##0.00')
        libro_id = self.env['fiscal.book'].browse(self._context['active_id'])
        row = 1
        col = 0
        date_start = datetime.strftime(datetime.strptime(str(self.date_start), DEFAULT_SERVER_DATE_FORMAT),
                                       format_new)
        date_end = datetime.strftime(datetime.strptime(str(self.date_end), DEFAULT_SERVER_DATE_FORMAT), format_new)
        writer.write_merge(row, row, 1, 5, 'Nombre de la Empresa: ' + libro_id.company_id.name, header_content_style_left)
        row += 1
        writer.write_merge(row, row, 1, 5, 'RIF.: ' + libro_id.company_id.vat, header_content_style_left)
        row += 1
        street = street2 = ''
        if libro_id.company_id.street:
            street = libro_id.company_id.street
        if libro_id.company_id.street2:
            street2 = ', ' + libro_id.company_id.street2
        writer.write_merge(row, row, 1, 5, 'Dirección de la Empresa: ' + street + street2, header_content_style_left)
        row += 1
        writer.write_merge(row, row, 1, 55, 'LIBRO DE COMPRAS', header_content_style)
        row += 1
        writer.write_merge(row, row, 1, 55, 'Desde: ' + date_start + ' Hasta: ' + date_end, header_content_style)
        row += 1
        #aca va pre encabezado
        writer.write_merge(row, row, 22, 41, "Compras Internas", sub_header_style)
        writer.write_merge(row, row, 42, 51, "Compras de Importaciones", sub_header_style)
        writer.write_merge(row, row, 52, 55, "Compras de Importaciones", sub_header_style)
        row += 1
        writer.write_merge(row, row, 1, 1, "Nro. Op", sub_header_style)
        writer.write_merge(row, row, 2, 3, "Fecha Emisión Doc.", sub_header_style)
        writer.write_merge(row, row, 4, 4, "Nro. de RIF", sub_header_style)
        writer.write_merge(row, row, 5, 6, "Nombre ó Razón Social", sub_header_style)
        writer.write_merge(row, row, 7, 7, "Tipo Prov.", sub_header_style)
        writer.write_merge(row, row, 8, 9, "Nro. de Factura", sub_header_style)
        writer.write_merge(row, row, 10, 11, "Nro. de Control", sub_header_style)
        writer.write_merge(row, row, 12, 13, "Nro. Nota de Crédito", sub_header_style)
        writer.write_merge(row, row, 14, 15, "Nro. Nota de Débito", sub_header_style)
        writer.write_merge(row, row, 16, 17, "Tipo de Trans", sub_header_style)
        writer.write_merge(row, row, 18, 19, "Nro. Factura Afectada", sub_header_style)
        writer.write_merge(row, row, 20, 21, "Total Compras con IVA", sub_header_style)
        writer.write_merge(row, row, 22, 23, "Compras sin Derecho a Crédito", sub_header_style)
        writer.write_merge(row, row, 24, 25, "Base Imponible Alicuota General", sub_header_style)
        writer.write_merge(row, row, 26, 27, "% Alicuota General", sub_header_style)
        writer.write_merge(row, row, 28, 29, "Impuesto (I.V.A) Alicuota General", sub_header_style)
        writer.write_merge(row, row, 30, 31, "Base Imponible Alicuota Reducida", sub_header_style)
        writer.write_merge(row, row, 32, 33, "% Alicuota Reducida", sub_header_style)
        writer.write_merge(row, row, 34, 35, "Impuesto (I.V.A) Alicuota Reducida", sub_header_style)
        writer.write_merge(row, row, 36, 37, "Base Imponible Alicuota Adicional", sub_header_style)
        writer.write_merge(row, row, 38, 39, "% Alicuota Adicional", sub_header_style)
        writer.write_merge(row, row, 40, 41, "Impuesto (I.V.A) Alicuota Adicional", sub_header_style)
        writer.write_merge(row, row, 42, 43, "Base Imponible Alicuota General", sub_header_style)
        writer.write_merge(row, row, 44, 45, "% Alicuota General", sub_header_style)
        writer.write_merge(row, row, 46, 47, "Impuesto (I.V.A) Alicuota General", sub_header_style)
        writer.write_merge(row, row, 48, 49, "Nro. Planilla Importación", sub_header_style)
        writer.write_merge(row, row, 50, 51, "Nro. Expediente Importación", sub_header_style)
        writer.write_merge(row, row, 52, 53, "Nro. de Comprobante", sub_header_style)
        writer.write_merge(row, row, 54, 55, "IVA Ret (Vend.)", sub_header_style)
        contador_2 = 0
        for datos in datos_compras:
            row += 1
            contador_2 += 1
            writer.write_merge(row, row, 1, 1, contador_2, sub_header_style_1)
            writer.write_merge(row, row, 2, 3, datos.get('emission_date'), sub_header_style_1)
            writer.write_merge(row, row, 4, 4, datos.get('partner_vat'), sub_header_style_1)
            writer.write_merge(row, row, 5, 6, datos.get('partner_name'), sub_header_style_1)
            writer.write_merge(row, row, 7, 7, datos.get('people_type'), sub_header_style_1)
            if datos.get('people_type') != 'N/DB':
                writer.write_merge(row, row, 8, 9, datos.get('invoice_number'), sub_header_style_1)
            writer.write_merge(row, row, 10, 11, datos.get('ctrl_number'), sub_header_style_1)
            if datos.get('doc_type') == 'N/DB':
                writer.write_merge(row, row, 12, 13, datos.get('invoice_number'), sub_header_style_1)
            writer.write_merge(row, row, 14, 15, datos.get('credit_affected'), sub_header_style_1)
            writer.write_merge(row, row, 16, 17, datos.get('type'), sub_header_style_1)
            if datos.get('doc_type') == 'N/DB':
                writer.write_merge(row, row, 18, 19, datos.get('affected_invoice'), sub_header_style_1)
            writer.write_merge(row, row, 20, 21, datos.get('total_with_iva'), sub_header_style_1)
            writer.write_merge(row, row, 22, 23, datos.get('vat_exempt'), sub_header_style_1)
            writer.write_merge(row, row, 24, 25, datos.get('vat_general_base'), sub_header_style_1)
            writer.write_merge(row, row, 26, 27, datos.get('vat_general_rate'), sub_header_style_1)
            writer.write_merge(row, row, 28, 29, datos.get('vat_general_tax'), sub_header_style_1)
            writer.write_merge(row, row, 30, 31, datos.get('vat_reduced_base'), sub_header_style_1)
            writer.write_merge(row, row, 32, 33, datos.get('vat_reduced_rate'), sub_header_style_1)
            writer.write_merge(row, row, 34, 35, datos.get('vat_reduced_tax'), sub_header_style_1)
            writer.write_merge(row, row, 36, 37, datos.get('vat_additional_base'), sub_header_style_1)
            writer.write_merge(row, row, 38, 39, datos.get('vat_additional_rate'), sub_header_style_1)
            writer.write_merge(row, row, 40, 41, datos.get('vat_additional_tax'), sub_header_style_1)
            writer.write_merge(row, row, 42, 43, datos.get('vat_general_base_importaciones'), sub_header_style_1)
            writer.write_merge(row, row, 44, 45, datos.get('vat_general_rate_importaciones'), sub_header_style_1)
            writer.write_merge(row, row, 46, 47, datos.get('vat_general_tax_importaciones'), sub_header_style_1)
            writer.write_merge(row, row, 48, 49, datos.get('nro_planilla'), sub_header_style_1)
            writer.write_merge(row, row, 50, 51, datos.get('nro_expediente'), sub_header_style_1)
            writer.write_merge(row, row, 52, 53, datos.get('wh_number'), sub_header_style_1)
            writer.write_merge(row, row, 54, 55, datos.get('get_wh_vat'), sub_header_style_1)

        row += 2
        writer.write_merge(row, row, 18, 19, "Totales", sub_header_style)
        writer.write_merge(row, row, 20, 21, sum_total_with_iva, sub_header_style)
        writer.write_merge(row, row, 22, 23, suma_vat_exempt, sub_header_style)
        writer.write_merge(row, row, 24, 25, sum_vat_general_base, sub_header_style)
        writer.write_merge(row, row, 26, 27, "", sub_header_style)
        writer.write_merge(row, row, 28, 29, sum_vat_general_tax, sub_header_style)
        writer.write_merge(row, row, 30, 31, sum_vat_reduced_base, sub_header_style)
        writer.write_merge(row, row, 32, 33, "", sub_header_style)
        writer.write_merge(row, row, 34, 35, sum_vat_reduced_tax, sub_header_style)
        writer.write_merge(row, row, 36, 37, sum_vat_additional_base, sub_header_style)
        writer.write_merge(row, row, 38, 39, "", sub_header_style)
        writer.write_merge(row, row, 40, 41, sum_vat_additional_tax, sub_header_style)
        writer.write_merge(row, row, 42, 43, sum_vat_general_base_importaciones, sub_header_style)
        writer.write_merge(row, row, 44, 45, "", sub_header_style)
        writer.write_merge(row, row, 46, 47, sum_vat_general_tax_importaciones, sub_header_style)
        writer.write_merge(row, row, 48, 49, "", sub_header_style)
        writer.write_merge(row, row, 50, 51, "", sub_header_style)
        writer.write_merge(row, row, 52, 53, "", sub_header_style)
        writer.write_merge(row, row, 54, 55, sum_get_wh_vat, sub_header_style)

        row += 2

        writer.write_merge(row, row, 4, 27, "RESUMEN DE LIBRO DE COMPRAS", sub_header_style_1)
        writer.write_merge(row, row, 28, 32, "Base Imponible", sub_header_style_1)
        writer.write_merge(row, row, 33, 37, "Crédito Fiscal", sub_header_style_1)
        row += 1
        writer.write_merge(row, row, 4, 27, "Compras Internas no Gravadas y/o Sin Derecho a Crédito Fiscal", sub_header_style_2)
        writer.write_merge(row, row, 28, 32, suma_vat_exempt, sub_header_style_1)
        writer.write_merge(row, row, 33, 37, 0.00, sub_header_style_1)
        row += 1
        writer.write_merge(row, row, 4, 27, "Compras Internas gravadas por Alicuota General", sub_header_style_2)
        writer.write_merge(row, row, 28, 32, sum_vat_general_base, sub_header_style_1)
        writer.write_merge(row, row, 33, 37, sum_vat_general_tax, sub_header_style_1)
        row += 1
        writer.write_merge(row, row, 4, 27, "Compras Internas gravadas por Alicuota General mas Alicuota Adicional", sub_header_style_2)
        writer.write_merge(row, row, 28, 32, sum_ali_gene_addi, sub_header_style_1)
        writer.write_merge(row, row, 33, 37, sum_ali_gene_addi_credit, sub_header_style_1)
        row += 1
        writer.write_merge(row, row, 4, 27, "Compras Internas gravadas por Alicuota Reducida", sub_header_style_2)
        writer.write_merge(row, row, 28, 32, sum_vat_reduced_base, sub_header_style_1)
        writer.write_merge(row, row, 33, 37, sum_vat_reduced_tax, sub_header_style_1)
        row += 1
        writer.write_merge(row, row, 4, 27, "Importaciones gravadas Alícuota General", sub_header_style_2)
        writer.write_merge(row, row, 28, 32, suma_base_general_importaciones, sub_header_style_1)
        writer.write_merge(row, row, 33, 37, sum_base_general_tax_importaciones, sub_header_style_1)
        row += 1
        writer.write_merge(row, row, 4, 27, "Importaciones gravadas por Alícuota General mas Adicional", sub_header_style_2)
        writer.write_merge(row, row, 28, 32, sum_ali_gene_addi_importaciones, sub_header_style_1)
        writer.write_merge(row, row, 33, 37, sum_ali_gene_addi_credit_importaciones, sub_header_style_1)
        row += 1
        writer.write_merge(row, row, 4, 27, "Importaciones gravadas por Alicuota Reducida", sub_header_style_2)
        writer.write_merge(row, row, 28, 32, sum_vat_reduced_base_importaciones, sub_header_style_1)
        writer.write_merge(row, row, 33, 37, sum_vat_reduced_tax_importaciones, sub_header_style_1)
        row += 1
        writer.write_merge(row, row, 4, 27, "Total Compras y Créditos Fiscales", sub_header_style_2)
        writer.write_merge(row, row, 28, 32, total_compras_base_imponible, sub_header_style_1)
        writer.write_merge(row, row, 33, 37, total_compras_credit_fiscal, sub_header_style_1)
        row += 1
        writer.write_merge(row, row, 4, 27, "Total IVA Retenido", sub_header_style_2)
        writer.write_merge(row, row, 28, 32, "", sub_header_style_1)
        writer.write_merge(row, row, 33, 37, sum_get_wh_vat, sub_header_style_1)

        wb.save(fp)
        out = base64.encodestring(fp.getvalue())
        self.write({'state': 'get', 'report': out, 'name': 'Libro de Compras.xls'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fiscal.book.wizard',
            'name': 'Fiscal Book Report',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    @api.model
    def xls_ventas(self):
        format_new = "%d/%m/%Y"

        # date_start =(str(self.date_start))
        # date_end =(str(self.date_end))

        fb_id = self._context['active_id']
        busq = self.env['fiscal.book'].search([('id','=',fb_id)])
        date_start = datetime.strptime(str(self.date_start), DATE_FORMAT).date()
        date_end = datetime.strptime(str(self.date_end), DATE_FORMAT).date()
        # date_start = busq.period_start
        # date_end = busq.period_end
        fbl_obj = self.env['fiscal.book.line'].search(
            [('fb_id','=',busq.id),('accounting_date', '>=', date_start)
             ])

        docs = []
        suma_total_w_iva = 0
        suma_no_taxe_sale = 0
        suma_vat_general_base = 0
        suma_total_vat_general_base = 0
        suma_total_vat_general_tax = 0
        suma_total_vat_reduced_base = 0
        suma_total_vat_reduced_tax = 0
        suma_total_vat_additional_base = 0
        suma_total_vat_additional_tax = 0
        suma_vat_general_tax = 0
        suma_vat_reduced_base = 0
        suma_vat_reduced_tax = 0
        suma_vat_additional_base = 0
        suma_vat_additional_tax = 0
        suma_get_wh_vat = 0
        suma_ali_gene_addi = 0
        suma_ali_gene_addi_debit = 0
        total_ventas_base_imponible = 0
        total_ventas_debit_fiscal = 0

        suma_amount_tax = 0

        for line in fbl_obj:
            if line.vat_general_base != 0 or line.vat_reduced_base != 0 or line.vat_additional_base != 0 or line.vat_exempt != 0:
                vat_general_base = 0
                vat_general_rate =  0
                vat_general_tax =  0
                vat_reduced_base = 0
                vat_additional_base =0
                vat_additional_rate = 0
                vat_additional_tax = 0
                vat_reduced_rate = 0
                vat_reduced_tax = 0


                if line.type == 'ntp':
                    no_taxe_sale = line.vat_general_base
                else:
                    no_taxe_sale = 0.0

                if line.vat_reduced_base and  line.vat_reduced_base != 0:
                    vat_reduced_base = line.vat_reduced_base
                    vat_reduced_rate = int(line.vat_reduced_base and line.vat_reduced_tax * 100 / line.vat_reduced_base)
                    vat_reduced_tax = line.vat_reduced_tax
                    suma_vat_reduced_base += line.vat_reduced_base
                    suma_vat_reduced_tax += line.vat_reduced_tax

                if line.vat_additional_base and line.vat_additional_base != 0:
                    vat_additional_base = line.vat_additional_base
                    vat_additional_rate = int(line.vat_additional_base and line.vat_additional_tax * 100 / line.vat_additional_base)
                    vat_additional_tax = line.vat_additional_tax
                    suma_vat_additional_base += line.vat_additional_base
                    suma_vat_additional_tax += line.vat_additional_tax

                if line.vat_general_base  and line.vat_general_base != 0:
                    vat_general_base = line.vat_general_base
                    vat_general_rate = int(line.vat_general_base and line.vat_general_tax * 100 / line.vat_general_base)
                    vat_general_tax = line.vat_general_tax
                    suma_vat_general_base += line.vat_general_base
                    suma_vat_general_tax += line.vat_general_tax



                if line.get_wh_vat:
                 suma_get_wh_vat += line.get_wh_vat
                if vat_reduced_rate == 0:
                    vat_reduced_rate = ''
                else:
                    vat_reduced_rate = str(vat_reduced_rate)
                if vat_additional_rate == 0:
                    vat_additional_rate = ''
                else:
                    vat_additional_rate = str(vat_additional_rate)
                if vat_general_rate == 0:
                    vat_general_rate = ''

                if  vat_general_rate == '' and vat_reduced_rate == '' and vat_additional_rate == '':
                    vat_general_rate = 0
                docs.append({
                    'rannk': line.rank,
                    'emission_date': datetime.strftime(datetime.strptime(str(line.emission_date), DEFAULT_SERVER_DATE_FORMAT), format_new),
                    'partner_vat': line.partner_vat if line.partner_vat else ' ',
                    'partner_name': line.partner_name,
                    'people_type': line.people_type if line.people_type else ' ',
                    'report_z': line.z_report,
                    'export_form': '',
                    'wh_number': line.wh_number,
                    'date_wh_number': line.iwdl_id.retention_id.date_ret if line.wh_number != '' else '',
                    'invoice_number': line.invoice_number,
                    'n_ultima_factZ': line.n_ultima_factZ,
                    'ctrl_number': line.ctrl_number,
                    'debit_note': '',
                    'credit_note': line.invoice_number if line.doc_type == 'N/CR' else '',
                    'type': line.void_form,
                    'affected_invoice': line.affected_invoice if line.affected_invoice else ' ',
                    'total_w_iva': line.total_with_iva if line.total_with_iva else 0,
                    'no_taxe_sale': line.vat_exempt,
                    'export_sale': '',
                    'vat_general_base': vat_general_base, # + vat_reduced_base + vat_additional_base,
                    'vat_general_rate': str(vat_general_rate), #+ '  ' + str(vat_reduced_rate) + ' ' + str(vat_additional_rate) + '  ',
                    'vat_general_tax': vat_general_tax, #+ vat_reduced_tax + vat_additional_tax,
                    'vat_reduced_base': line.vat_reduced_base,
                    'vat_reduced_rate': str(vat_reduced_rate),
                    'vat_reduced_tax': vat_reduced_tax,
                    'vat_additional_base': vat_additional_base,
                    'vat_additional_rate': str(vat_additional_rate),
                    'vat_additional_tax': vat_additional_tax,
                    'get_wh_vat': line.get_wh_vat,
                })

                suma_total_w_iva += line.total_with_iva
                suma_no_taxe_sale += line.vat_exempt
                suma_total_vat_general_base += line.vat_general_base
                suma_total_vat_general_tax +=  line.vat_general_tax
                suma_total_vat_reduced_base +=  line.vat_reduced_base
                suma_total_vat_reduced_tax += line.vat_reduced_tax
                suma_total_vat_additional_base += line.vat_additional_base
                suma_total_vat_additional_tax += line.vat_additional_tax

                #RESUMEN LIBRO DE VENTAS


               # suma_ali_gene_addi =  suma_vat_additional_base if line.vat_additional_base else 0.0
                #suma_ali_gene_addi_debit = suma_vat_additional_tax if line.vat_additional_tax else 0.0
                total_ventas_base_imponible = suma_vat_general_base + suma_vat_additional_base + suma_vat_reduced_base + suma_no_taxe_sale
                total_ventas_debit_fiscal = suma_vat_general_tax + suma_vat_additional_tax + suma_vat_reduced_tax

        #///////////////////////////////////////GENERANDO EXCEL////////////////////////////////////////////////////////
        fp = BytesIO()
        wb = xlwt.Workbook(encoding='utf-8')
        writer = wb.add_sheet('Nombre de hoja')
        xlwt.add_palette_colour("custom_colour", 0x21)
        wb.set_colour_RGB(0x21, 164,164,164)
        header_content_style = xlwt.easyxf("font: name Helvetica size 40 px, bold 1, height 200; align: horiz center;")
        header_content_style_left = xlwt.easyxf("font: name Helvetica size 40 px, bold 1, height 200; align: horiz left;")
        sub_header_style_1 = xlwt.easyxf(
            "font: name Helvetica size 10 px, bold 1, height 170; borders: left thin, right thin, top thin, bottom thin; align: horiz center;")
        sub_header_style = xlwt.easyxf(
            "font: name Helvetica size 10 px, bold 1, height 170; borders: left thin, right thin, top thin, bottom thin; align: horiz center; pattern: pattern solid,fore_colour custom_colour;")  # color pattern: pattern solid,fore_colour blue;
        sub_header_style_2 = xlwt.easyxf(
            "font: name Helvetica size 10 px, bold 1, height 170; borders: left thin, right thin, top thin, bottom thin; align: horiz left;")

        line_content_style_totales = xlwt.easyxf(
            "font: name Helvetica size 10 px, bold 1, height 170; borders: left thin, right thin, top thin, bottom thin; align: horiz right;",
            num_format_str='#,##0.00')
        libro_id = self.env['fiscal.book'].browse(self._context['active_id'])
        row = 1
        col = 0
        date_start = datetime.strftime(datetime.strptime(str(self.date_start), DEFAULT_SERVER_DATE_FORMAT),
                                       format_new)
        date_end = datetime.strftime(datetime.strptime(str(self.date_end), DEFAULT_SERVER_DATE_FORMAT), format_new)
        writer.write_merge(row, row, 1, 5, 'Nombre de la Empresa: ' + libro_id.company_id.name, header_content_style_left)
        row += 1
        writer.write_merge(row, row, 1, 5, 'RIF.: ' + libro_id.company_id.vat, header_content_style_left)
        row += 1
        street = street2 = ''
        if libro_id.company_id.street:
            street = libro_id.company_id.street
        if libro_id.company_id.street2:
            street2 = ', ' + libro_id.company_id.street2
        writer.write_merge(row, row, 1, 5, 'Dirección de la Empresa: ' + street + street2, header_content_style_left)
        row += 1
        writer.write_merge(row, row, 1, 55, 'LIBRO DE VENTAS', header_content_style)
        row += 1
        writer.write_merge(row, row, 1, 55, 'Desde: ' + date_start + ' Hasta: ' + date_end, header_content_style)
        row += 1
        #aca va pre encabezado
        writer.write_merge(row, row, 24, 41, "Ventas Internas ó Exportación Gravadas", sub_header_style)

        row += 1
        writer.write_merge(row, row, 1, 1, "Nro. Op", sub_header_style)
        writer.write_merge(row, row, 2, 3, "Fecha Documento", sub_header_style)
        writer.write_merge(row, row, 4, 4, "RIF", sub_header_style)
        writer.write_merge(row, row, 5, 6, "Nombre ó Razón Social", sub_header_style)
        writer.write_merge(row, row, 7, 7, "Tipo Prov.", sub_header_style)
        writer.write_merge(row, row, 8, 9, "Nro. Planilla de Exportación", sub_header_style)
        writer.write_merge(row, row, 10, 11, "Nro. De Factura", sub_header_style)
        writer.write_merge(row, row, 12, 13, "Nro. De Control", sub_header_style)
        writer.write_merge(row, row, 14, 15, "Nro. Factura Afectada", sub_header_style)
        writer.write_merge(row, row, 16, 17, "Nro. Nota de Débito", sub_header_style)
        writer.write_merge(row, row, 18, 19, "Nro. Nota de Crédito", sub_header_style)
        writer.write_merge(row, row, 20, 21, "Tipo de Trans.", sub_header_style)
        writer.write_merge(row, row, 22, 23, "Ventas Incluyendo IVA", sub_header_style)
        writer.write_merge(row, row, 24, 25, "Ventas Internas ó Exportaciones No Gravadas", sub_header_style)
        writer.write_merge(row, row, 26, 27, "Ventas Internas ó Exportaciones Exoneradas", sub_header_style)
        writer.write_merge(row, row, 28, 29, "Base Imponible Alicuota General", sub_header_style)
        writer.write_merge(row, row, 30, 31, "% Alícuota General", sub_header_style)
        writer.write_merge(row, row, 32, 33, "Impuesto IVA Alicuota General", sub_header_style)
        writer.write_merge(row, row, 34, 35, "Base Imponible Alicuota Reducida", sub_header_style)
        writer.write_merge(row, row, 36, 37, "% Alícuota Reducida", sub_header_style)
        writer.write_merge(row, row, 38, 39, "Impuesto IVA Alicuota Reducida", sub_header_style)
        writer.write_merge(row, row, 40, 41, "Base Imponible Alicuota Adicional", sub_header_style)
        writer.write_merge(row, row, 42, 43, "% Alícuota Adicional", sub_header_style)
        writer.write_merge(row, row, 44, 45, "Impuesto IVA Alicuota Adicional", sub_header_style)
        writer.write_merge(row, row, 46, 47, "IVA Retenido (Comprador)", sub_header_style)
        writer.write_merge(row, row, 48, 49, "Nro. De Comprobante", sub_header_style)
        writer.write_merge(row, row, 50, 51, "Fecha Comp.", sub_header_style)
        contador_2 = 0
        for datos in docs:
            row += 1
            contador_2 += 1
            writer.write_merge(row, row, 1, 1, contador_2, sub_header_style_1)
            writer.write_merge(row, row, 2, 3, datos.get('emission_date'), sub_header_style_1)
            writer.write_merge(row, row, 4, 4, datos.get('partner_vat'), sub_header_style_1)
            writer.write_merge(row, row, 5, 6, datos.get('partner_name'), sub_header_style_1)
            writer.write_merge(row, row, 7, 7, datos.get('people_type'), sub_header_style_1)
            writer.write_merge(row, row, 8, 9, datos.get('export_form'), sub_header_style_1)
            if not datos.get('credit_note'):
                writer.write_merge(row, row, 10, 11, datos.get('invoice_number'), sub_header_style_1)
            writer.write_merge(row, row, 12, 13, datos.get('ctrl_number'), sub_header_style_1)
            writer.write_merge(row, row, 14, 15, datos.get('affected_invoice'), sub_header_style_1)
            writer.write_merge(row, row, 16, 17, datos.get('debit_note'), sub_header_style_1)
            writer.write_merge(row, row, 18, 19, datos.get('credit_note'), sub_header_style_1)
            writer.write_merge(row, row, 20, 21, datos.get('type'), sub_header_style_1)
            writer.write_merge(row, row, 22, 23, datos.get('total_w_iva'), sub_header_style_1)
            writer.write_merge(row, row, 24, 25, datos.get('no_taxe_sale'), sub_header_style_1)
            writer.write_merge(row, row, 26, 27, datos.get('export_sale'), sub_header_style_1)
            writer.write_merge(row, row, 28, 29, datos.get('vat_general_base'), sub_header_style_1)
            if datos.get('vat_general_rate') != '':
                writer.write_merge(row, row, 30, 31, datos.get('vat_general_rate') + '%', sub_header_style_1)
            writer.write_merge(row, row, 32, 33, datos.get('vat_general_tax'), sub_header_style_1)
            writer.write_merge(row, row, 34, 35, datos.get('vat_reduced_base'), sub_header_style_1)
            if datos.get('vat_reduced_rate') != '':
                writer.write_merge(row, row, 36, 37, datos.get('vat_reduced_rate') + '%', sub_header_style_1)
            writer.write_merge(row, row, 38, 39, datos.get('vat_reduced_tax'), sub_header_style_1)
            writer.write_merge(row, row, 40, 41, datos.get('vat_additional_base'), sub_header_style_1)
            if datos.get('vat_additional_rate') != '':
                writer.write_merge(row, row, 42, 43, datos.get('vat_additional_rate') + '%', sub_header_style_1)
            writer.write_merge(row, row, 44, 45, datos.get('vat_additional_tax'), sub_header_style_1)
            writer.write_merge(row, row, 46, 47, datos.get('get_wh_vat'), sub_header_style_1)
            writer.write_merge(row, row, 48, 49, datos.get('wh_number'), sub_header_style_1)
            writer.write_merge(row, row, 50, 51, datos.get('date_wh_number'), sub_header_style_1)

        row += 2
        writer.write_merge(row, row, 20, 21, "Totales", sub_header_style)
        writer.write_merge(row, row, 22, 23, suma_total_w_iva, sub_header_style)
        writer.write_merge(row, row, 24, 25, suma_no_taxe_sale, sub_header_style)
        writer.write_merge(row, row, 26, 27, 0.00, sub_header_style)
        writer.write_merge(row, row, 28, 29, suma_total_vat_general_base, sub_header_style)
        writer.write_merge(row, row, 30, 31, "", sub_header_style)
        writer.write_merge(row, row, 32, 33, suma_total_vat_general_tax, sub_header_style)
        writer.write_merge(row, row, 34, 35, suma_total_vat_reduced_base, sub_header_style)
        writer.write_merge(row, row, 36, 37, "", sub_header_style)
        writer.write_merge(row, row, 38, 39, suma_total_vat_reduced_tax, sub_header_style)
        writer.write_merge(row, row, 40, 41, suma_total_vat_additional_base, sub_header_style)
        writer.write_merge(row, row, 42, 43, "", sub_header_style)
        writer.write_merge(row, row, 44, 45, suma_total_vat_additional_tax, sub_header_style)
        writer.write_merge(row, row, 46, 47, suma_get_wh_vat, sub_header_style)

        row += 2

        writer.write_merge(row, row, 5, 10, "RESUMEN DE LIBRO DE VENTAS", sub_header_style_1)
        writer.write_merge(row, row, 11, 13, "Base Imponible", sub_header_style_1)
        writer.write_merge(row, row, 14, 16, "Debito Fiscal", sub_header_style_1)
        writer.write_merge(row, row, 17, 19, "IVA Retenido por el Comprador", sub_header_style_1)
        row += 1
        writer.write_merge(row, row, 5, 10, "Ventas Internas Exoneradas", sub_header_style_2)
        writer.write_merge(row, row, 11, 13, suma_no_taxe_sale, sub_header_style_1)
        writer.write_merge(row, row, 14, 16, 0.00, sub_header_style_1)
        writer.write_merge(row, row, 17, 19, 0.00, sub_header_style_1)
        row += 1
        writer.write_merge(row, row, 5, 10, "Ventas de Exportación", sub_header_style_2)
        writer.write_merge(row, row, 11, 13, 0.00, sub_header_style_1)
        writer.write_merge(row, row, 14, 16, 0.00, sub_header_style_1)
        writer.write_merge(row, row, 17, 19, 0.00, sub_header_style_1)
        row += 1
        writer.write_merge(row, row, 5, 10, "Ventas Internas gravadas por Alicuota General", sub_header_style_2)
        writer.write_merge(row, row, 11, 13, suma_vat_general_base, sub_header_style_1)
        writer.write_merge(row, row, 14, 16, suma_vat_general_tax, sub_header_style_1)
        writer.write_merge(row, row, 17, 19, suma_get_wh_vat, sub_header_style_1)
        row += 1
        writer.write_merge(row, row, 5, 10, "Ventas Internas gravadas por Alicuota General mas Alicuota Adicional", sub_header_style_2)
        writer.write_merge(row, row, 11, 13, suma_ali_gene_addi, sub_header_style_1)
        writer.write_merge(row, row, 14, 16, suma_ali_gene_addi_debit, sub_header_style_1)
        writer.write_merge(row, row, 17, 19, 0.00, sub_header_style_1)
        row += 1
        writer.write_merge(row, row, 5, 10, "Ventas Internas gravadas por Alicuota Reducida", sub_header_style_2)
        writer.write_merge(row, row, 11, 13, suma_vat_reduced_base, sub_header_style_1)
        writer.write_merge(row, row, 14, 16, suma_vat_reduced_tax, sub_header_style_1)
        writer.write_merge(row, row, 17, 19, 0.00, sub_header_style_1)
        row += 1
        writer.write_merge(row, row, 5, 10, "Total Ventas y Debitos Fiscales", sub_header_style_2)
        writer.write_merge(row, row, 11, 13, total_ventas_base_imponible, sub_header_style_1)
        writer.write_merge(row, row, 14, 16, total_ventas_debit_fiscal, sub_header_style_1)
        writer.write_merge(row, row, 17, 19, suma_get_wh_vat, sub_header_style_1)

        wb.save(fp)
        out = base64.encodestring(fp.getvalue())
        self.write({'state': 'get', 'report': out, 'name': 'Libro de Ventas.xls'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'fiscal.book.wizard',
            'name': 'Fiscal Book Report',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

        return

    def obtener_tasa(self, invoice):
        fecha = invoice.date
        tasa_id = invoice.currency_id
        tasa = self.env['multi.currency.rate'].search([('currency_id', '=', tasa_id.id), ('rate_date', '<=', fecha)], order='id desc', limit=1)
        if not tasa:
            raise exceptions.except_orm("Advertencia!",
                                        "No hay referencia de tasas registradas para moneda USD en la fecha igual o inferior de la factura %s" %(invoice.name))

        return tasa.rate
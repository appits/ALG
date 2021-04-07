# coding: utf-8
##############################################################################

###############################################################################
import time

from odoo import fields, models, api, exceptions, _
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from datetime import datetime, date, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class WizardReport_1(models.TransientModel):  # aqui declaro las variables del wizar que se usaran para el filtro del pdf
    _name = 'wizard.resumen.iva'
    _description = "Resumen Retenciones IVA"

    date_from = fields.Date('Date From', default=lambda *a: (datetime.now() - timedelta(days=(1))).strftime('%Y-%m-%d'))
    date_to = fields.Date(string='Date To', default=lambda *a: datetime.now().strftime('%Y-%m-%d'))
    date_actual = fields.Date(default=lambda *a: datetime.now().strftime('%Y-%m-%d'))

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)

    def print_resumen_iva(self):
        
        data = {
            'model': 'report.l10n_ve_resumen_retenciones.libro_resumen_iva',
            'form': {
                #        'datas': datas,
                'date_from': self.date_from,
                'date_to': self.date_to,
                'date_actual': self.date_actual,
            },
            'company_id': self.company_id.id,
            #  'context': self._context
        }
        return self.env.ref('l10n_ve_resumen_retenciones.libr_resumen_iva').report_action(self,
                                                                                   data=data)  # , config=False
       

class ReportResumenIva(models.AbstractModel):

    _name = 'report.l10n_ve_resumen_retenciones.libro_resumen_iva'

    @api.model
    def _get_report_values(self, docids, data=None):
        format_new = "%d/%m/%Y"
        company_id = data['company_id']
        company_id = self.env['res.company'].search([('id','=',company_id)])
        date_from = datetime.strptime(data['form']['date_from'], DATE_FORMAT)
        date_to = datetime.strptime(data['form']['date_to'], DATE_FORMAT)
        date_actual = datetime.strptime(data['form']['date_actual'], DATE_FORMAT)
        docs=[]
        cursor_resumen = self.env['account.move'].search([
            ('date','>=',date_from),
            ('date','<=',date_to),
            ('state','in',('posted','cancel' )),
            ('type','in',('in_invoice','in_refund','in_receipt'))
            ],order="invoice_date asc")
        date_from = datetime.strftime(datetime.strptime(data['form']['date_from'], DEFAULT_SERVER_DATE_FORMAT),
                                       format_new)
        date_to = datetime.strftime(datetime.strptime(data['form']['date_to'], DEFAULT_SERVER_DATE_FORMAT), format_new)
        date_actual = datetime.strftime(datetime.strptime(data['form']['date_actual'], DEFAULT_SERVER_DATE_FORMAT), format_new)
        cont = 0
        for det in cursor_resumen:
            if det.wh_iva_id:
                sale_total = det.wh_iva_id.amount_base_ret + det.wh_iva_id.total_tax_ret
                iva = det.wh_iva_id.total_tax_ret
                iva_retenido = (det.wh_iva_id.total_tax_ret * det.wh_iva_id.wh_lines[0].wh_iva_rate) / 100
                alicuota_general = alicuota_reducida = alicuota_adicional = sdcf = alicuota_reducida_monto = alicuota_general_adicional = alicuota_general_adicional_monto =0
                alicuota_general_adicional_monto = porcentaje_alicuota_general_adicional = alicuota_adicional_monto = alicuota_general_monto= 0
                base_general = base_reducida = base_adicional = ''
                for ali in det.invoice_line_ids:
                    for imp in ali.tax_ids:
                        if imp.appl_type == 'general':
                            alicuota_general += ali.price_subtotal
                            alicuota_general_monto = (alicuota_general * imp.amount) / 100
                            base_general = str(imp.amount) + '%'
                        if imp.appl_type == 'reducido':
                            alicuota_reducida += ali.price_subtotal
                            alicuota_reducida_monto = (alicuota_reducida * imp.amount) /100
                            base_reducida = str(imp.amount) + '%'
                        if imp.appl_type == 'adicional':
                            alicuota_adicional += ali.price_subtotal
                            alicuota_adicional_monto = (alicuota_adicional * imp.amount) / 100
                            porcentaje_alicuota_general_adicional = imp.amount
                            base_adicional = str(imp.amount) + '%'
                        if imp.appl_type == 'exento':
                            sdcf += ali.price_subtotal
                alicuota_general_adicional = alicuota_adicional
                if alicuota_general_adicional > 0 and porcentaje_alicuota_general_adicional > 0:
                    alicuota_general_adicional_monto = (alicuota_general_adicional * porcentaje_alicuota_general_adicional) / 100
                alicuota_totales = (alicuota_general_monto * det.wh_iva_id.wh_lines.wh_iva_rate) / 100


                # if det.wh_iva_id.type == 'in_refund' or det.wh_iva_id.type == 'in_receipt':
                if company_id.partner_id.company_type == 'person':
                    rif_empresa = company_id.partner_id.nationality
                else:
                    rif_empresa = company_id.partner_id.vat
                cont += 1
                ref_v = ''
                if det.type == 'in_invoice' and det.debit_origin_id:
                    ref_v = det.debit_origin_id.supplier_invoice_number
                if det.type == 'in_refund':
                    ref_v = det.invoice_reverse_purchase_id.supplier_invoice_number
                tipo_doc = ''
                sign = 1
                if det.wh_iva_id.type == 'in_invoice' or det.wh_iva_id.type =='out_invoice':
                    tipo_doc = '01'
                if det.wh_iva_id.type == 'in_refund' or det.wh_iva_id.type =='out_refund':
                    tipo_doc = '03'
                    sign = -1
                if det.wh_iva_id.type == 'in_debit' or det.wh_iva_id.type =='out_debit':
                    tipo_doc = '02'



                date_factura = datetime.strftime(
                    datetime.strptime(str(det.invoice_date), DEFAULT_SERVER_DATE_FORMAT), format_new)
                docs.append({
                'cont': cont,
                'name':date_factura,
                'document':det.name,
                'partner_identification': det.partner_id.vat if det.partner_id.vat else det.partner_id.identification_id ,
                'partner_name': det.partner_id.name,
                'invoice_number': det.supplier_invoice_number,
                'tipo_doc': tipo_doc,
                'invoice_ctrl_number': det.nro_ctrl,
                'sale_total': sale_total * sign,
                'base_imponible': det.amount_untaxed * sign,
                'iva' : iva * sign,
                'iva_retenido': iva_retenido,
                'retenido': det.wh_iva_id.name,
                'retenido_date':det.wh_iva_id.date,
                'state_retantion': det.wh_iva_id.state,
                'state': det.state,
                'currency_id':det.currency_id.id,
                'ref':ref_v,
                'total_exento':sdcf * sign,
                'alicuota_reducida':alicuota_reducida,
                'alicuota_general': alicuota_general * sign,
                'alicuota_adicional': alicuota_adicional * sign,
                'alicuota_reducida_monto': alicuota_reducida_monto * sign,
                'alicuota_general_monto': alicuota_general_monto  * sign,
                'alicuota_adicional_monto': alicuota_adicional_monto * sign,
                'alicuota_totales': alicuota_totales  * sign,
                'base_adicional': base_adicional,
                'base_reducida': base_reducida,
                'base_general': base_general,
                'retenido_reducida': alicuota_reducida,
                'retenido_adicional': alicuota_adicional,
                'retenido_general': alicuota_general,
                'vat_ret_id':det.wh_iva_id.id,
                'invoice_id':det.id,
                'tax_id': '',
                'alicuota_general_adicional':alicuota_general_adicional,
                'porcentaje_alicuota_general_adicional': porcentaje_alicuota_general_adicional,
                'alicuota_general_adicional_monto': alicuota_general_adicional_monto,
                'numero_comprobante': det.wh_iva_id.number if det.wh_iva_id.number else '',

                })
        return {
            'doc_model': data['model'],
            'docs': docs,
            'rif_company': rif_empresa,
            'name_company': company_id.name,
            'date_actual': date_actual,
            'date_from': date_from,
            'date_to': date_to,
            

        }
#

from datetime import datetime, timedelta
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT

from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError
import openerp.addons.decimal_precision as dp
import logging

import io
from io import BytesIO

import xlsxwriter
import shutil
import base64
import csv
import xlwt
import xml.etree.ElementTree as ET

class LibroComprasModelo(models.Model):
    _name = "resumen.iva.wizard.pdf"

    name = fields.Date(string='Fecha')
    document = fields.Char(string='Rif')
    partner  = fields.Many2one(comodel_name='res.partner', string='Partner')
    invoice_number =   fields.Char(string='invoice_number')
    tipo_doc = fields.Char(string='tipo_doc')
    invoice_ctrl_number = fields.Char(string='invoice_ctrl_number')
    sale_total = fields.Float(string='invoice_ctrl_number')
    base_imponible = fields.Float(string='invoice_ctrl_number')
    iva = fields.Float(string='iva')
    iva_retenido = fields.Float(string='iva retenido')
    retenido = fields.Char(string='retenido')
    retenido_date = fields.Date(string='date')
    alicuota = fields.Char(string='alicuota')
    alicuota_type = fields.Char(string='alicuota type')
    state_retantion = fields.Char(string='state')
    state = fields.Char(string='state')
    reversed_entry_id = fields.Many2one('account.move', string='Facturas', store=True)
    currency_id = fields.Many2one('res.currency', 'Currency')
    ref = fields.Char(string='ref')

    total_exento = fields.Float(string='Total Excento')
    alicuota_reducida = fields.Float(string='Alicuota Reducida')
    alicuota_general = fields.Float(string='Alicuota General')
    alicuota_adicional = fields.Float(string='Alicuota General + Reducida')

    base_general = fields.Float(string='Total Base General')
    base_reducida = fields.Float(string='Total Base Reducida')
    base_adicional = fields.Float(string='Total Base General + Reducida')

    retenido_general = fields.Float(string='retenido General')
    retenido_reducida = fields.Float(string='retenido Reducida')
    retenido_adicional = fields.Float(string='retenido General + Reducida')

    vat_ret_id = fields.Many2one('vat.retention', string='Nro de Comprobante IVA')
    invoice_id = fields.Many2one('account.move')
    tax_id = fields.Many2one('account.tax', string='Tipo de Impuesto')


    def float_format(self,valor):
        #valor=self.base_tax
        if valor:
            result = '{:,.2f}'.format(valor)
            result = result.replace(',','*')
            result = result.replace('.',',')
            result = result.replace('*','.')
        else:
            result="0,00"
        return result

    def formato_fecha2(self,date):
        fecha = str(date)
        fecha_aux=fecha
        ano=fecha_aux[0:4]
        mes=fecha[5:7]
        dia=fecha[8:10]  
        resultado=dia+"/"+mes+"/"+ano
        return resultado

    def rif2(self,aux):
        #nro_doc=self.partner_id.vat
        busca_partner = self.env['res.partner'].search([('id','=',aux)])
        if busca_partner:
            for det in busca_partner:
                if busca_partner.company_type == 'person':
                    tipo_doc = busca_partner.nationality
                else:
                    tipo_doc = busca_partner.vat[0]
                if busca_partner.vat:
                    nro_doc=str(busca_partner.vat)
                else:
                    nro_doc='0000000000'
        else:
            nro_doc='000000000'
            tipo_doc='V'
        nro_doc=nro_doc.replace('V','')
        nro_doc=nro_doc.replace('v','')
        nro_doc=nro_doc.replace('E','')
        nro_doc=nro_doc.replace('e','')
        nro_doc=nro_doc.replace('G','')
        nro_doc=nro_doc.replace('g','')
        nro_doc=nro_doc.replace('J','')
        nro_doc=nro_doc.replace('j','')
        nro_doc=nro_doc.replace('P','')
        nro_doc=nro_doc.replace('p','')
        nro_doc=nro_doc.replace('c','')
        nro_doc=nro_doc.replace('C','')
        nro_doc=nro_doc.replace('-','')
        
        if tipo_doc=="v":
            tipo_doc="V"
        if tipo_doc=="e":
            tipo_doc="E"
        if tipo_doc=="g":
            tipo_doc="G"
        if tipo_doc=="j":
            tipo_doc="J"
        if tipo_doc=="p":
            tipo_doc="P"
        if tipo_doc=="c":
            tipo_doc="C"
        resultado=str(tipo_doc)+"-"+str(nro_doc)
        return resultado

class WizardReport_1(models.TransientModel): # aqui declaro las variables del wizar que se usaran para el filtro del pdf
    _name = 'wizard.resumen.iva'
    _description = "Resumen Retenciones IVA"

    date_from  = fields.Date('Date From', default=lambda *a:(datetime.now() - timedelta(days=(1))).strftime('%Y-%m-%d'))
    date_to = fields.Date(string='Date To', default=lambda *a:datetime.now().strftime('%Y-%m-%d'))
    date_actual = fields.Date(default=lambda *a:datetime.now().strftime('%Y-%m-%d'))

    company_id = fields.Many2one('res.company','Company',default=lambda self: self.env.user.company_id.id)
    line  = fields.Many2many(comodel_name='resumen.iva.wizard.pdf', string='Lineas')

    def rif(self,aux):
        #nro_doc=self.partner_id.vat
        busca_partner = self.env['res.partner'].search([('id','=',aux)])
        for det in busca_partner:
            if busca_partner.company_type == 'person':
                tipo_doc = busca_partner.nationality
            else:
                tipo_doc = busca_partner.vat[0]
            nro_doc=str(busca_partner.vat)
        nro_doc=nro_doc.replace('V','')
        nro_doc=nro_doc.replace('v','')
        nro_doc=nro_doc.replace('E','')
        nro_doc=nro_doc.replace('e','')
        nro_doc=nro_doc.replace('G','')
        nro_doc=nro_doc.replace('g','')
        nro_doc=nro_doc.replace('J','')
        nro_doc=nro_doc.replace('j','')
        nro_doc=nro_doc.replace('P','')
        nro_doc=nro_doc.replace('p','')
        nro_doc=nro_doc.replace('-','')
        
        if tipo_doc=="v":
            tipo_doc="V"
        if tipo_doc=="e":
            tipo_doc="E"
        if tipo_doc=="g":
            tipo_doc="G"
        if tipo_doc=="j":
            tipo_doc="J"
        if tipo_doc=="p":
            tipo_doc="P"
        if tipo_doc=="c":
            tipo_doc="C"
        resultado=str(tipo_doc)+"-"+str(nro_doc)
        return resultado

    def periodo(self,date):
        fecha = str(date)
        fecha_aux=fecha
        mes=fecha[5:7] 
        resultado=mes
        return resultado

    def formato_fecha(self,date):
        fecha = str(date)
        fecha_aux=fecha
        ano=fecha_aux[0:4]
        mes=fecha[5:7]
        dia=fecha[8:10]  
        resultado=dia+"/"+mes+"/"+ano
        return resultado

    def float_format2(self,valor):
        #valor=self.base_tax
        if valor:
            result = '{:,.2f}'.format(valor)
            result = result.replace(',','*')
            result = result.replace('.',',')
            result = result.replace('*','.')
        else:
            result="0,00"
        return result

    def conv_div_nac(self,valor,selff):
        selff.invoice_id.currency_id.id
        fecha_contable_doc=selff.invoice_id.date
        monto_factura=selff.invoice_id.amount_total
        valor_aux=0
        #raise UserError(_('moneda compañia: %s')%self.company_id.currency_id.id)
        if selff.invoice_id.currency_id.id!=self.company_id.currency_id.id:
            tasa= self.env['account.move'].search([('id','=',selff.invoice_id.id)],order="id asc")
            for det_tasa in tasa:
                monto_nativo=det_tasa.amount_untaxed_signed
                monto_extran=det_tasa.amount_untaxed
                valor_aux=abs(monto_nativo/monto_extran)
            rate=round(valor_aux,2)  # LANTA
            #rate=round(valor_aux,2)  # ODOO SH
            resultado=valor*rate
        else:
            resultado=valor
        return resultado

    def get_invoice(self):
        t=self.env['resumen.iva.wizard.pdf']
        d=t.search([])
        d.unlink()
        cursor_resumen = self.env['account.move'].search([
            ('invoice_date','>=',self.date_from),
            ('invoice_date','<=',self.date_to),
            ('state','in',('posted','cancel' )),
            ('type','in',('in_invoice','in_refund','in_receipt'))
            ])
        for det in cursor_resumen:
            if det.wh_iva_id:
                sale_total = det.wh_iva_id.amount_base_ret + det.wh_iva_id.total_tax_ret
                iva = det.wh_iva_id.total_tax_ret
                iva_retenido = (det.wh_iva_id.total_tax_ret * det.wh_iva_id.wh_lines[0].wh_iva_rate) / 100
                alicuota_general = alicuota_reducida = alicuota_adicional = sdcf = 0
                base_general = base_reducida = base_adicional = ''
                for ali in det.invoice_line_ids:
                    for imp in ali.tax_ids:
                        if imp.appl_type == 'general':
                            alicuota_general += ali.price_subtotal
                            base_general = imp.amount
                        if imp.appl_type == 'reducido':
                            alicuota_reducida += ali.price_subtotal
                            base_reducida = imp.amount
                        if imp.appl_type == 'adicional':
                            alicuota_adicional += ali.price_subtotal
                            base_adicional = imp.amount
                        if imp.appl_type == 'sdcf':
                            sdcf += ali.price_subtotal

                values={
                'name':det.invoice_date,
                'document':det.name,
                'partner':det.partner_id.id,
                'invoice_number': det.supplier_invoice_number,#darrell
                'tipo_doc': det.wh_iva_id.type,
                'invoice_ctrl_number': det.nro_ctrl,
                'sale_total': sale_total,
                'base_imponible': det.amount_untaxed,
                'iva' : iva,
                'iva_retenido': iva_retenido,
                'retenido': det.wh_iva_id.name,
                'retenido_date':det.wh_iva_id.date,
                'state_retantion': det.wh_iva_id.state,
                'state': det.state,
                'currency_id':det.currency_id.id,
                'ref':det.ref,
                'total_exento':0,
                'alicuota_reducida':alicuota_reducida,
                'alicuota_general': alicuota_general,
                'alicuota_adicional': alicuota_adicional,
                'base_adicional': base_adicional,
                'base_reducida': base_reducida,
                'base_general': base_general,
                'retenido_reducida': alicuota_reducida,
                'retenido_adicional': alicuota_adicional,
                'retenido_general': alicuota_general,
                'vat_ret_id':det.wh_iva_id.id,
                'invoice_id':det.id,
                'tax_id': '',
                }
                pdf_id = t.create(values)
                hola = 454
            #   temp = self.env['account.wizard.pdf.ventas'].search([])
        self.line = self.env['resumen.iva.wizard.pdf'].search([])

    def print_resumen_iva(self):
        self.get_invoice()
        #return self.env.ref('libro_ventas.libro_factura_clientes').report_action(self)
        return {'type': 'ir.actions.report','report_name': 'l10n_ve_resumen_retenciones.libro_resumen_iva','report_type':"qweb-pdf"}
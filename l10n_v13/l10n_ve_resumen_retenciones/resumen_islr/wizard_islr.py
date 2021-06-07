from datetime import datetime, timedelta
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
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


class WizardReport_2(models.TransientModel): # aqui declaro las variables del wizar que se usaran para el filtro del pdf
    _name = 'wizard.resumen.islr'
    _description = "Resumen Retenciones islr"

    date_from  = fields.Date('Date From', default=lambda *a:(datetime.now() - timedelta(days=(1))).strftime('%Y-%m-%d'))
    date_to = fields.Date(string='Date To', default=lambda *a:datetime.now().strftime('%Y-%m-%d'))
    date_actual = fields.Date(default=lambda *a:datetime.now().strftime('%Y-%m-%d'))

    company_id = fields.Many2one('res.company','Company',default=lambda self: self.env.user.company_id.id)
    #line_people  = fields.Many2many(comodel_name='islr.wh.doc', string='Lineas')


    def print_resumen_islr(self):
        #pass
        data = {
            'model': 'report.l10n_ve_resumen_retenciones.libro_resumen_islr',
            'form': {
                #        'datas': datas,
                'date_from': self.date_from,
                'date_to': self.date_to,
                'date_actual': self.date_actual,
            },
            'company_id': self.company_id.id,
            #  'context': self._context
        }
        return self.env.ref('l10n_ve_resumen_retenciones.libr_resumen_islr').report_action(self,
                                                                                          data=data)  # , config=False

    class ReportResumenIslr(models.AbstractModel):
        _name = 'report.l10n_ve_resumen_retenciones.libro_resumen_islr'

        @api.model
        def _get_report_values(self, docids, data=None):
            format_new = "%d/%m/%Y"
            company_id = data['company_id']
            company_id = self.env['res.company'].search([('id', '=', company_id)])
            date_from = datetime.strptime(data['form']['date_from'], DATE_FORMAT)
            date_to = datetime.strptime(data['form']['date_to'], DATE_FORMAT)
            date_actual = datetime.strptime(data['form']['date_actual'], DATE_FORMAT)
            docs = []
            
            varc = 'xxxxxxx'
            docs.append({
                'fecha': varc,
                'f_factura': varc,
                'nro_factura': varc,
                'rif': varc,
                'name_proveedor': varc,
                'codigo': varc,
                'abono_cta': 22,
                'cant_retencion': 222,
                'porcentaje': 22,
                'retencion_total': 22222,
            })

            if company_id.partner_id.company_type == 'person':
                rif_empresa = company_id.partner_id.nationality
            else:
                rif_empresa = company_id.partner_id.vat
            return {
                'doc_model': data['model'],
                'docs': docs,
                'rif_company': rif_empresa,
                'name_company': company_id.name,
                'date_actual': date_actual,
                'date_from': date_from,
                'date_to': date_to,
                'total': varc,
                'total_2': varc,
                'definir': varc

            }
from odoo import api, fields, models


class ResPartner(models.Model):

    _inherit = 'res.partner'

    margin = fields.Float(string='Margin(%)')
    margin_valor = fields.Float(string='Margin Valor($/Kg)')
    max_diff = fields.Float(string='Maximum Difference in Rate Allowed', default='0')


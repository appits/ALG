from odoo import fields, models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    percent_margin = fields.Float()
    margin_amount = fields.Float()
    percent_additional = fields.Float()
    base_calculation = fields.Selection(selection=[
        ('min', 'Minimum'),
        ('max', 'Maximum'),
        ('mp', 'Market Price')
    ], required=True, copy=False, default='mp')


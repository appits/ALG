from odoo import fields, models, api


class Product(models.Model):
    _inherit = 'product.template'

    is_micro_manual = fields.Boolean(default=True)

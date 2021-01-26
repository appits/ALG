from odoo import fields, models, api


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    product_type = fields.Selection([
        ('PT', 'End Product'),
        ('SE', 'Semi-Finished')
    ], copy=False, store=True)

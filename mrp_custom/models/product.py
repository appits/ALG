from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    generate_production = fields.Boolean(default=False, copy=False)
    plan_production = fields.Boolean(default=False, copy=False)
    location_picking_id = fields.Many2one('stock.location')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    generate_production = fields.Boolean(default=False, copy=False, related='product_tmpl_id.generate_production', store=True)
    plan_production = fields.Boolean(default=False, copy=False, related='product_tmpl_id.plan_production', store=True)
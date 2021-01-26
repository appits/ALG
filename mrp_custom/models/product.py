from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    generate_production = fields.Boolean(default=False, copy=False)

    @api.constrains('generate_production')
    def set_gen_product(self):
        product = self.env['product.product'].search([('product_tmpl_id.id', '=', self.id)])
        product.generate_production = self.generate_production


class ProductProduct(models.Model):
    _inherit = 'product.product'

    generate_production = fields.Boolean(default=False, copy=False)

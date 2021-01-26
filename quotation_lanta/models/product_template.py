from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    price_market = fields.Float(copy=False)
    is_operating_cost = fields.Boolean(copy=False, default=False)

    @api.constrains('is_operating_cost')
    def validate_product_cost(self):
        location = self.env['product.template'].search([('is_operating_cost', '=', True)])
        number = 0
        for record in location:
            number += 1
        if number > 1:
            raise ValidationError(_('You cannot have more than one operating cost product'))
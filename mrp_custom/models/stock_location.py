from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class StockLocation(models.Model):
    _inherit = 'stock.location'

    transit_location = fields.Boolean(default=False, copy=False)

    @api.constrains('transit_location')
    def validate_transit(self):
        location = self.env['stock.location'].search([('transit_location', '=', True)])
        number = 0
        for record in location:
            number += 1
        if number > 1:
            raise ValidationError(_('It cannot have more than one transitory location'))



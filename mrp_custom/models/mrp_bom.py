from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    batch_controlled = fields.Boolean(default=True, copy=False)
    capacity_batch = fields.Float(default=0)


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    @api.onchange('product_id')
    def validate_product(self):
        for record in self:
            if record.product_id.product_tmpl_id == record.bom_id.product_tmpl_id:
                raise ValidationError(_(
                    'The product selected in the list cannot be the same as the product to be produced'))

from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    percentage_of_loss = fields.Float()
    list_for_quotation = fields.Boolean()
    quantity_sum_raw = fields.Float(
        'Quantity', default=1.0,
        digits='Unit of Measure')

    @api.constrains('list_for_quotation')
    def evaluate_quot_mark(self):
        for record in self:
            bom = record.env['mrp.bom'].search(
                [('product_tmpl_id', '=', record.product_tmpl_id.id), ('list_for_quotation', '=', True)])
            bom_count = len(bom)
            if bom_count > 1:
                raise ValidationError(_(
                    'You cannot have more than one BOM per product marked for quotation'))

    @api.onchange('bom_line_ids')
    def sum_components(self):
        components = 0
        for lines in self.bom_line_ids:
            if (lines.product_id.categ_id.send_sicbatch or lines.product_id.bom_ids) and self.type == 'normal':
                components += lines.product_qty
        self.quantity_sum_raw = components

    @api.constrains('quantity_sum_raw')
    def validate_qty_raw(self):
        for record in self:
            if record.product_qty != record.quantity_sum_raw:
                raise ValidationError(_(
                    'The sum of the raw materials has to match the quantity to be produced, validate the lines of the list of materials'))


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    @api.constrains('product_uom_id')
    def validate_uom(self):
        for record in self:
            if record.product_id.categ_id.send_sicbatch and record.bom_id.company_id.control_bom:
                if record.product_uom_id != record.bom_id.product_uom_id:
                    raise ValidationError(_(
                        'The product cannot have a unit of measure other than the final product, the product is: %s' % record.product_id.name))





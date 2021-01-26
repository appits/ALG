from odoo import _, fields, models, api
from odoo.exceptions import UserError


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    product_packaging_id = fields.Many2one('product.packaging')
    qty_packaging = fields.Float()

    @api.constrains('picking_id')
    def get_value_lines(self):
        if self.picking_id.purchase_id:
            for record in self:
                lines = record.env['purchase.order.line'].search([('product_id.id', '=', record.product_id.id), (
                    'order_id.id', '=', record.picking_id.purchase_id.id)])
                if lines:
                    for order_line in lines:
                        record.product_packaging_id = order_line.product_packaging_id
                        if record.product_packaging_id and record.product_packaging_id.qty > 0:
                            record.qty_packaging = (record.product_qty / record.product_packaging_id.qty)
        elif self.picking_id.sale_id:
            for record in self:
                lines = record.env['sale.order.line'].search([('product_id.id', '=', record.product_id.id),
                                                              ('order_id.id', '=', record.picking_id.sale_id.id)])
                if lines:
                    for order_line in lines:
                        record.product_packaging_id = order_line.product_packaging
                        if record.product_packaging_id and record.product_packaging_id.qty > 0:
                            record.qty_packaging = (record.product_qty / record.product_packaging_id.qty)


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_packaging_id = fields.Many2one('product.packaging')
    qty_packaging = fields.Float()

    @api.constrains('picking_id')
    def get_value_lines(self):
        if self.picking_id.purchase_id:
            for record in self:
                lines = record.env['purchase.order.line'].search([('product_id.id', '=', record.product_id.id), (
                    'order_id.id', '=', record.picking_id.purchase_id.id)])
                if lines:
                    for order_line in lines:
                        record.product_packaging_id = order_line.product_packaging_id
                        if record.product_packaging_id and record.product_packaging_id.qty > 0:
                            record.qty_packaging = (record.product_qty / record.product_packaging_id.qty)
        elif self.picking_id.sale_id:
            for record in self:
                lines = record.env['sale.order.line'].search([('product_id.id', '=', record.product_id.id),
                                                              ('order_id.id', '=', record.picking_id.sale_id.id)])
                if lines:
                    for order_line in lines:
                        record.product_packaging_id = order_line.product_packaging
                        if record.product_packaging_id and record.product_packaging_id.qty > 0:
                            record.qty_packaging = (record.product_qty / record.product_packaging_id.qty)
            return record


class Packing(models.Model):
    _inherit = 'product.packaging'

    @api.constrains('qty')
    def validate_qty(self):
        for record in self:
            if record.qty == 0:
                raise UserError(_('No puede dejar el valor en 0'))

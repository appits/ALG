from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    transport = fields.Char()
    car_plate = fields.Char()
    date_driver = fields.Char()
    identification_driver = fields.Char()
    loading_note = fields.Char()
    invoice_reverse_id = fields.Many2one('account.move', string="Reversal invoice", copy=False)
    invoice_reverse_purchase_id = fields.Many2one('account.move', string="Reversal invoice purchase", copy=False)

    @api.onchange('invoice_reverse_id', 'invoice_reverse_purchase_id')
    def set_reference(self):
        for record in self:
            if record.type in ('out_refund', 'out_receipt'):
                continue
                #record.ref = record.invoice_reverse_id.invoice_number_cli
            elif record.type in ('in_refund', 'in_receipt'):
                continue
                # record.ref = record.invoice_reverse_purchase_id.invoice_number_pro

    @api.model
    def create(self, vals):
        result = super(AccountMove, self).create(vals)
        if result.type == 'out_invoice':
            order = result.env['sale.order'].search([('name', '=', result.invoice_origin)])
            picking = result.env['stock.picking'].search([('sale_id.id', '=', order.id)])
            for record in picking:
                result.transport = record.transport
                result.car_plate = record.car_plate
                result.date_driver = record.date_driver
                result.identification_driver = record.identification_driver
        return result

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for lines in self.invoice_line_ids:
            lines.price_string = False
            for lines_tax in lines.tax_ids:
                if lines_tax.amount == 0:
                    lines.price_string = str(lines.price_unit) + ' (E)'
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    product_packaging_id = fields.Many2one('product.packaging')
    price_string = fields.Char()
    dose_kgton = fields.Float()

    def create(self, vals):
        result = super(AccountMoveLine, self).create(vals)
        for lines in result:
            order = lines.env['sale.order'].search([('name', '=', lines.move_id.invoice_origin)])
            order_line = lines.env['sale.order.line'].search(
                [('order_id.id', '=', order.id), ('product_id.id', '=', lines.product_id.id)])
            if result.product_id:
                for record in order_line:
                    result.product_packaging_id = record.product_packaging.id
                    result.dose_kgton = record.dose_kgton
            return result

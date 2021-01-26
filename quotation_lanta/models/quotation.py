from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class Quotation(models.Model):
    _name = 'quotation'

    sale_order_id = fields.Many2one('sale.order', ondelete="cascade")
    sale_order_line_id = fields.Many2one('sale.order.line', ondelete="cascade")
    product_id = fields.Many2one('product.product')
    qty_bom = fields.Float(digits=(0, 5))
    total_percent_lost = fields.Float(digits=(0, 5))
    cost_operating = fields.Float(digits=(0, 5))
    cost_input = fields.Float(digits=(0, 5))
    cost_raw_input = fields.Float(digits=(0, 5))
    primary_cost = fields.Float(digits=(0, 5))
    total_cost = fields.Float(digits=(0, 5))
    percent_partner_additional = fields.Float(digits=(0, 5))
    total_percent_partner_additional = fields.Float(digits=(0, 5))
    percent_gain = fields.Float(digits=(0, 5))
    dollar_k = fields.Float(digits=(0, 5))
    result_percent_gain = fields.Float(digits=(0, 5))
    result_total = fields.Float(digits=(0, 5))
    price_quotation = fields.Float(digits=(0, 5))
    price_kg = fields.Float(digits=(0, 5))
    cost_kg = fields.Float(digits=(0, 5))
    profit_kg = fields.Float(digits=(0, 5))
    percent_profit_kg = fields.Float(digits=(0, 5))
    percent_cost_profit_kg = fields.Float(digits=(0, 5))
    quotation_line_ids = fields.One2many('quotation.line', 'quotation_id',
                                         domain=[('product_id.categ_id.send_sicbatch', '=', True)], )
    quotation_input_ids = fields.One2many('quotation.line', 'quotation_id',
                                          domain=[('product_id.categ_id.send_sicbatch', '=', False)], )
    base_calculation = fields.Selection(selection=[
        ('min', 'Minimum'),
        ('max', 'Maximum'),
        ('mp', 'Market Price')
    ], required=True, copy=False, default='mp')
    processed = fields.Boolean(default=False)

    def recalculate_price(self):
        for lines in self.sale_order_line_id:
            if lines.product_id and lines.product_id.bom_ids:
                bom = lines.env['mrp.bom'].search(
                    [('product_tmpl_id', '=', lines.product_id.product_tmpl_id.id), ('list_for_quotation', '=', True)])
                if not bom:
                    raise ValidationError(_(
                        'El producto seleccionado no contiene lista de materiales para cotizacion, por favor configure una lista para seguir el proceso, el producto es: %s' % str(
                            lines.product_id.name)))

            price_quo = lines.create_and_update_lines_quotation(bom, self)
            lines.price_unit = price_quo


class QuotationLine(models.Model):
    _name = 'quotation.line'

    name = fields.Char()
    quotation_id = fields.Many2one('quotation')
    product_id = fields.Many2one('product.product')
    price_min = fields.Float(digits=(0, 5))
    price_max = fields.Float(digits=(0, 5))
    price_market = fields.Float(digits=(0, 5))
    qty_component = fields.Float(digits=(0, 5))
    percentage_of_loss = fields.Float(digits=(0, 5))

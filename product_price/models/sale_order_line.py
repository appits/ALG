from odoo import api, fields, models
from datetime import timedelta
from odoo.tools import float_round


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        pro_vendor = self.env['product.supplierinfo']
        bom_obj = self.env['mrp.bom']
        operation_cost = vendor_price = 0
        for line in self:
            vendor_prices = pro_vendor.search([('product_tmpl_id', '=', line.product_id.product_tmpl_id.id), ('date_end', '>=', fields.Date.today()-timedelta(days=line.company_id.days)), ('date_end', '>=', fields.Date.today())])
            if vendor_prices:
                vendor_price = max(vendor_prices.mapped('price')) 
            bom = bom_obj.search([('product_id', '=', line.product_id.id)])
            if not bom:
                bom = bom_obj.search([('product_tmpl_id', '=', line.product_id.product_tmpl_id.id)])
            if bom:
                bom = bom[0]
                if bom.product_qty > 0:
                    total = new_total = 0.0
                    for operation in bom.routing_id.operation_ids:
                        operation_cycle = float_round(float_round(bom.product_uom_id._compute_quantity(bom.product_qty, bom.product_uom_id) / bom.product_qty, precision_rounding=1, rounding_method='UP') / operation.workcenter_id.capacity, precision_rounding=1,
                                                      rounding_method='UP')
                        duration_expected = operation_cycle * operation.time_cycle + operation.workcenter_id.time_stop + operation.workcenter_id.time_start
                        total = ((duration_expected / 60.0) * operation.workcenter_id.costs_hour)

                        new_total += self.company_id.currency_id.round(total)
                    operation_cost = new_total
            
            total_price = vendor_price + operation_cost
            op1 = total_price*(line.order_partner_id.margin/100)
            op2 = total_price*line.order_partner_id.margin_valor
            line.price_unit = max(op1, op2)
            return res

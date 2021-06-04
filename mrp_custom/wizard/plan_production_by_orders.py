from odoo import fields, models, api
from ..utils import utils


class PlanOrders(models.TransientModel):
    _name = 'plan.production.by.order'
    _description = 'Production Plan by Orders'

    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    orders_ids = fields.Many2many('sale.order')

    def process_value(self):
        for order in self.orders_ids.filtered_domain([('process', '=', True)]):
            productions = []
            for lines in order.order_line:
                if lines.product_id.plan_production:
                    if lines.product_id.bom_ids:
                        self_prod = lines.env['mrp.production']
                        production = utils.generate_production(order, lines.product_id, lines.product_uom_qty,
                                                               order.warehouse_id, order.name, lines.product_uom.id,
                                                               0)
                        main_prod = self_prod.search([('id', 'in', production)])
                        for main in main_prod:
                            child_production = self_prod.search([('origin', '=', main.name)])
                            if child_production:
                                productions += child_production.ids

                        productions += main_prod.ids

            order.write({'production_ids': productions,
                         'mrp_processed': True})
        return {
            'type': 'ir.actions.client',
            'name': 'Point of Sale Menu',
            'tag': 'reload',
            'params': {'menu_id': self.env.ref('mrp.menu_mrp_root').id},
        }

    @api.model
    def default_get(self, fields):
        vals = super(PlanOrders, self).default_get(fields)
        if vals:
            domain = [('order_id.company_id', '=', vals['company_id']),
                      ('order_id.state', 'in', ('sale', 'done')),
                      ('order_id.mrp_processed', '=', False),
                      ('order_id.production_ids', '=', False),
                      ('product_id.plan_production', '=', True)]
            orders = self.env['sale.order.line'].read_group(domain, ['price_subtotal', 'order_id'],
                                                            ['order_id'])
            if orders:
                order_ids = []
                for o in orders:
                    order = self.env['sale.order'].search([('id', '=', o['order_id'][0])])
                    order.process = False
                    order_ids += [order.id]
                vals.update({'orders_ids': order_ids})
        return vals

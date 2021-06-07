from odoo import _, fields, models, api
from odoo.exceptions import AccessError, UserError, ValidationError
from ..utils import utils


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    production_ids = fields.Many2many('mrp.production', copy=False)
    production_count = fields.Integer(compute="count_production", string="Productions")
    mrp_processed = fields.Boolean(default=False, copy=False)
    process = fields.Boolean(default=False, copy=False)

    def count_production(self):
        production = []
        number = 0
        for record in self.production_ids:
            production += [record.id]
        if self.production_ids:
            query = 'select count(id) from mrp_production where id in'
            string_production = (str(production).replace('[', '(').replace(']', ')'))
            query_execute = query + string_production
            self._cr.execute(query_execute)
            value = self._cr.fetchall()
            for count in value:
                number = count[0]
        self['production_count'] = number

    def call_production(self):
        action = self.env.ref('mrp.mrp_production_action').read()[0]
        production = []
        for record in self.production_ids:
            production += [record.id]
        (str(production).replace('[', '(').replace(']', ')'))
        action['domain'] = [('id', 'in', production)]
        return action

    def action_confirm(self):
        productions = []
        production = []
        for lines in self.order_line:
            self_prod = lines.env['mrp.production']
            if lines.product_id.generate_production:
                if lines.product_id.bom_ids:
                    production = utils.generate_production(self, lines.product_id, lines.product_uom_qty, self.warehouse_id, self.name, lines.product_uom.id, 0)

        if production:
            productions += production
            main_prod = self_prod.search([('id', 'in', production)])
            for main in main_prod:
                child_prod = self_prod.search([('origin', '=', main.name)])
                if child_prod:
                    productions += child_prod.ids
            self.production_ids = productions
        res = super(SaleOrder, self).action_confirm()
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_uom_qty')
    def validate_qty_production(self):
        for lines in self:
            number_max = 10
            if lines.product_id.bom_ids:
                bom = []
                for bom_id in lines.product_id.bom_ids:
                    if not bom:
                        bom = bom_id

                if bom.routing_id:
                    if bom.capacity_batch > 0:
                        qty_loop = lines.product_uom_qty
                        turns_qty = 0
                        while qty_loop > 0:
                            if qty_loop > bom.product_qty:
                                qty_to_produce = bom.capacity_batch
                                turns_qty += 1
                            else:
                                qty_to_produce = qty_loop
                                turns_qty += 1

                            qty_loop -= qty_to_produce

                        if turns_qty >= number_max:
                            message = _('Ten precaucion, el producto a vender generará: %s producciones' % (
                                str(turns_qty)))
                            mess = {'title': _('Warning production!'),
                                    'message': message
                                    }
                            return {'warning': mess}

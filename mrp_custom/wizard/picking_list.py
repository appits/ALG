from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class PickingList(models.TransientModel):
    _name = 'picking.list'
    _description = 'Groups the inputs of the productions to be generated'

    def default_production(self):
        productions = self.env['mrp.production'].search(
            [('processed_picking_list', '=', False), ('state', 'in', ('draft', 'confirmed'))])
        return productions

    production_ids = fields.Many2many('mrp.production', default=default_production,
                                      domain="[('processed_picking_list', '=', False), ('state', 'in', ('draft', 'confirmed'))]")
    location_id = fields.Many2one('stock.location')
    location_dest_id = fields.Many2one('stock.location')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
    warehouse_id = fields.Many2one('stock.warehouse')
    warning_ids = fields.One2many('picking.warning', 'picking_list_id')

    def get_qty_production_movement(self):

        if self.production_ids:
            picking_id = self.env['stock.picking'].create({'partner_id': self.company_id.partner_id.id,
                                                           'move_type': 'direct',
                                                           'state': 'draft',
                                                           'generated_by_picking_list': True,
                                                           'location_id': self.location_id.id,
                                                           'location_dest_id': self.location_dest_id.id,
                                                           'picking_type_id': self.warehouse_id.int_type_id.id,
                                                           'company_id': self.company_id.id,
                                                           'is_locked': False})
            production_generator = []
            product_id = []
            for production in self.production_ids:
                production_generator += [production.id]
                production.processed_picking_list = True
                production.pick_ids = picking_id

                for raw in self.production_ids.move_raw_ids:
                    if not raw.product_id.bom_ids:
                        product_id += [raw.product_id.id]

            picking_id.production_ids = production_generator
            query = 'select product_id, sum(product_uom_qty) from stock_move where raw_material_production_id in'
            string_production = (str(production_generator).replace('[', '(').replace(']',
                                                                                     ')')) + 'and product_id in ' + (
                                    str(product_id).replace('[', '(').replace(']', ')')) + 'group by product_id'
            query_execute = query + string_production
            self._cr.execute(query_execute)
            value = self._cr.fetchall()

            for sqls in value:
                product_id = self.env['product.product'].search([('id', '=', sqls[0])])
                self.env['stock.move'].create({'name': product_id.name,
                                               'state': picking_id.state,
                                               'priority': '1',
                                               'location_id': self.location_id.id,
                                               'location_dest_id': self.location_dest_id.id,
                                               'picking_type_id': self.warehouse_id.int_type_id.id,
                                               'partner_id': picking_id.partner_id.id,
                                               'company_id': picking_id.company_id.id,
                                               'product_id': product_id.id,
                                               'description_picking': product_id.name,
                                               'product_uom_qty': sqls[1],
                                               'product_uom': product_id.uom_id.id,
                                               'picking_id': picking_id.id,
                                               'procure_method': 'make_to_stock',
                                               'reference': picking_id.name,
                                               'unit_factor': 1})

            self.production_ids = [(5, 0, 0)]
            return picking_id


class PickingWarning(models.TransientModel):
    _name = 'picking.warning'

    picking_list_id = fields.Many2one('picking.list')

    def generate_movement(self):
        picking_id = self.picking_list_id.get_qty_production_movement()
        if picking_id:
            target_form = self.env.ref('stock.view_picking_form')
            return {
                'name': 'Stock Picking',
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'res_id': picking_id.id,
                'view_id.id': target_form.id,
                'view_mode': 'form',
                'target': 'current'
            }
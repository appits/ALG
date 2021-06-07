from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


def generate_production(self, product_id, qty, warehouse_id, related_document, uom_id, location_dest_id):
    if product_id.bom_ids:
        bom = []
        for bom_id in product_id.bom_ids:
            if not bom:
                bom = bom_id

        qty_on_hand = self.env['stock.quant'].search([
            ('product_id', '=', product_id.id),
            ('location_id', '=', warehouse_id.out_type_id.default_location_src_id.id),
        ])

        quantity = 0
        reserved_quantity = 0
        for quant in qty_on_hand:
            quantity += quant.quantity
            reserved_quantity += quant.reserved_quantity

        stock = quantity - reserved_quantity

        if stock > 0:
            qty_actual = qty - stock
        else:
            qty_actual = qty

        productions = []
        if qty_actual > 0:
            if bom.routing_id and bom.capacity_batch > 0 and bom.batch_controlled:
                if self.sudo().env.ref('product.decimal_product_uom'):
                    precision_digits = self.sudo().env.ref('product.decimal_product_uom').digits
                else:
                    precision_digits = 2

                qty_loop = qty_actual
                while qty_loop > 0:
                    if qty_loop > bom.capacity_batch:
                        qty_to_produce = bom.capacity_batch
                    else:
                        qty_to_produce = qty_loop

                    if warehouse_id.manu_type_id.active:

                        if location_dest_id > 0:
                            loc = location_dest_id
                        else:
                            loc = warehouse_id.manu_type_id.default_location_dest_id.id

                        production = create_production(self,
                                                       related_document,
                                                       product_id.id,
                                                       product_id.product_tmpl_id.id,
                                                       uom_id,
                                                       qty_to_produce,
                                                       bom.id,
                                                       warehouse_id.manu_type_id.id,
                                                       warehouse_id.manu_type_id.default_location_src_id.id,
                                                       loc)
                        qty_loop -= qty_to_produce
                        qty_loop = round(qty_loop, precision_digits)
                        productions += [production.id]
                        production._onchange_move_raw()
                        production.action_confirm()
                    else:
                        raise ValidationError(_(
                            'The type of manufacturing operation of this warehouse is archived, please choose another warehouse or un-archive the type of operation and re-process'))
            else:
                if warehouse_id.manu_type_id.active:

                    if location_dest_id > 0:
                        loc = location_dest_id
                    else:
                        loc = warehouse_id.manu_type_id.default_location_dest_id.id

                    production = create_production(self,
                                                   related_document,
                                                   product_id.id,
                                                   product_id.product_tmpl_id.id,
                                                   uom_id,
                                                   qty_actual,
                                                   bom.id,
                                                   warehouse_id.manu_type_id.id,
                                                   warehouse_id.manu_type_id.default_location_src_id.id,
                                                   loc)
                    productions += [production.id]
                    production._onchange_move_raw()
                    production.action_confirm()

                else:
                    raise ValidationError(_(
                        'The type of manufacturing operation of this warehouse is archived, please choose another warehouse or un-archive the type of operation and re-process'))

    return productions


def create_production(self, name, product_id, product_tmpl_id, product_uom_id, product_qty, bom_id, picking_type_id,
                      location_src_id, location_dest_id):
    production = self.env['mrp.production'].create({'origin': name,
                                                    'state': 'draft',
                                                    'product_id': product_id,
                                                    'product_tmpl_id': product_tmpl_id,
                                                    'product_uom_id': product_uom_id,
                                                    'product_qty': product_qty,
                                                    'bom_id': bom_id,
                                                    'picking_type_id': picking_type_id,
                                                    'location_src_id': location_src_id,
                                                    'location_dest_id': location_dest_id,
                                                    'order_id': self.id})
    return production

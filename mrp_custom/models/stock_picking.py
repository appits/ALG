from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    generated_by_picking_list = fields.Boolean()
    related_picking_id = fields.Many2one('stock.picking')
    generated_by_related = fields.Boolean()
    production_ids = fields.Many2many('mrp.production', copy=False)
    production_count = fields.Integer(compute="count_production", string="Productions")

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

    def action_done(self):
        res = super(StockPicking, self).action_done()
        location_to_id = self.env['stock.location'].search([('transit_location', '=', True)])
        validation = 0
        for location_validation in location_to_id:
            validation += 1

        if location_to_id:
            if validation == 1:
                if self.generated_by_picking_list:
                    picking_id = self.env['stock.picking'].create({'partner_id': self.company_id.partner_id.id,
                                                                   'move_type': 'direct',
                                                                   'state': 'draft',
                                                                   'related_picking_id': self.id,
                                                                   'generated_by_related': True,
                                                                   'location_id': self.location_dest_id.id,
                                                                   'location_dest_id': self.location_dest_id.id,
                                                                   'picking_type_id': self.picking_type_id.id,
                                                                   'company_id': self.company_id.id,
                                                                   'production_ids': self.production_ids})
                    for picking_line in self.move_ids_without_package:
                        picking_line.env['stock.move'].create({'name': picking_line.product_id.name,
                                                               'state': picking_id.state,
                                                               'priority': '1',
                                                               'location_id': picking_line.location_dest_id.id,
                                                               'location_dest_id': location_validation.id,
                                                               'picking_type_id': picking_id.picking_type_id.id,
                                                               'partner_id': picking_id.partner_id.id,
                                                               'company_id': picking_id.company_id.id,
                                                               'product_id': picking_line.product_id.id,
                                                               'description_picking': picking_line.product_id.name,
                                                               'product_uom_qty': picking_line.product_uom_qty,
                                                               'product_uom': picking_line.product_uom.id,
                                                               'picking_id': picking_id.id,
                                                               'procure_method': 'make_to_stock',
                                                               'reference': picking_id.name,
                                                               'unit_factor': 1})
                    self.related_picking_id = picking_id.id

                    for production in self.production_ids:
                        production.write({'pick_ids': [(4, picking_id.id, _)]})
            else:
                raise ValidationError(_('You cannot have more than one temporary location, please validate'))

        else:
            raise ValidationError(_('you must configure a transient location'))

        return res

    def action_confirm(self):
        res = super(StockPicking, self).action_confirm()
        if self.generated_by_related:
            for record_related in self.move_ids_without_package:
                if record_related.location_dest_id.transit_location:
                    raise ValidationError(_('you cannot validate a record with transient locations, please validate'))
                if record_related.location_dest_id.id == record_related.location_id.id:
                    raise ValidationError(_('you cannot make a move to the same location, please change'))
        return res

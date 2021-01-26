from odoo import fields, models, api, _
from odoo.exceptions import UserError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def action_print(self):
        if self.state == 'done':
            for record in self.finished_move_line_ids:

                self.env.cr.execute(
                    'delete from mrp_print where mrp_id= %s',
                    [self.id])

                n = self.bom_id.numbers_bom
                if n > 0:
                    while n > 0:
                        create = record.env['mrp.print'].create({'mrp_id': self.id,
                                                                 'bom_id': self.bom_id.id,
                                                                 'nro': n,
                                                                 'product_packaging_id': self.bom_id.product_packaging_id.id,
                                                                 'product_id': record.product_id.id,
                                                                 'lot_id': record.lot_id.id,
                                                                 'date': record.lot_id.use_date,
                                                                 'date_f': self.date_planned_start,
                                                                 'routing_id': self.routing_id.id,
                                                                 })
                        n -= 1

            data = self.env['mrp.print'].search([('mrp_id.id', '=', self.id)])
            return self.env.ref('reports_lanta.report_mrp_production').report_action(data)


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    numbers_bom = fields.Integer(default=1)
    product_packaging_id = fields.Many2one('product.packaging')

    @api.constrains('numbers_bom')
    def validate_number(self):
        if self.numbers_bom == 0:
            raise UserError(_('No puede dejar el valor en 0'))

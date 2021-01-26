from odoo import fields, models, api, _
from odoo.exceptions import UserError


class Inventory(models.Model):
    _inherit = 'stock.inventory'

    numbers_labels = fields.Float(default=1)

    @api.constrains('numbers_labels')
    def validate_number(self):
        if self.numbers_labels == 0:
            raise UserError(_('No puede dejar el valor en 0'))

    def action_print(self):
        if self.state == 'confirm':
            lines = self.env['stock.inventory.line'].search([('inventory_id.id', '=', self.id)])

            self.env.cr.execute(
                'delete from stock_print where inventory_id= %s',
                [self.id])

            n_t = 0
            for record in lines:
                n = self.numbers_labels
                n_d = 0
                n_t += 1
                while n > 0:
                    last = False
                    n_d += 1
                    if n_d == self.numbers_labels:
                        last = True
                    create = record.env['stock.print'].create({'inventory_id': record.inventory_id.id,
                                                               'inventory_line_id': record.id,
                                                               'code': record.product_id.default_code,
                                                               'nro_total': n_t,
                                                               'nro': n_d,
                                                               'last': last,
                                                               'product_id': record.product_id.id,
                                                               'lot_id': record.prod_lot_id.id,
                                                               'date': record.inventory_id.accounting_date,
                                                               'location_id': record.location_id.id,
                                                               })
                    n -= 1
            data = self.env['stock.print'].search([('inventory_id.id', '=', self.id)])
            return self.env.ref('reports_lanta.report_label').report_action(data)



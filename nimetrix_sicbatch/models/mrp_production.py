import sys

import requests

from odoo import fields, models, api, _
from odoo.exceptions import UserError

from odoo.addons.nimetrix_sicbatch.models import utils


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    order_id = fields.Many2one('sale.order')
    id = fields.Integer()

    @api.model
    def create(self, vals):
        if 'origin' in vals:
            sales_order = self.env['sale.order'].search(
                [('name', '=', vals['origin'])])
            vals['order_id'] = sales_order.id

            if not sales_order:
                production_order = self.env['mrp.production'].search(
                    [('name', '=', vals['origin'])])
                vals['order_id'] = production_order.order_id.id

        result = super(MrpProduction, self).create(vals)
        return result

    def button_mark_done(self):
        res = super(MrpProduction, self).button_mark_done()
        config = utils.get_config(self)
        url = config.server
        self.ensure_one()
        lines = self.env['stock.move'].search([
            ('raw_material_production_id', '=', self.id)
        ])

        for line in lines:
            if line.product_id.product_tmpl_id.categ_id.send_sicbatch and line.location_id.send_sicbatch \
                    and line.sicbatch_lot:

                stocks = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', line.location_id.id),
                    ('lot_id', '=', line.sicbatch_lot.vendor_lot_id.id)
                ])

                for stock in stocks:

                    if stock.quantity <= 0:
                        try:
                            data = {
                                'name': "spLotes_Actualizar",
                                'param1': line.sicbatch_lot.sequence_lot
                            }
                            response = requests.post(url=url, json=data)
                            if response.status_code == 200:
                                connection = True
                        except requests.exceptions.ConnectTimeout:
                            raise UserError(_("Error al conectar a Sicbatch"))

        return res

    def call_wizard(self):
        target_form = self.env.ref('nimetrix_sicbatch.sicbatch_orders_act_window')

        try:
            config = utils.get_config(self)
            url = config.server
            connection = True
            seq = config.sequence_manual
            name = config.sequence_manual.next_by_code(seq.code)

            data = {
                'name': "spOrdenProduccion_Manual_GET",
                'param1': name
            }

            response = requests.post(url=url, json=data)

            if response != 200:
                raise UserError(_("No se puede conectar a Sicbatch"))
            else:
                rows = response.json()

            order = self.env['sicbatch.orders'].create({
                'production_id': self.id,
            })
            count = 0

            for row in rows:
                lines = self.env['sicbatch.orders.lines'].create({
                    'sicbatch_id': order.id,
                    'order_id': int(str(row[0]).strip()),
                    'client_name': str(row[2].strip()),
                    'product_value': str(row[3]).strip(),
                    'product_name': str(row[4]).strip(),
                    'selected': False
                })

            return {
                'name': 'Sicbatch',
                'type': 'ir.actions.act_window',
                'res_model': 'sicbatch.orders',
                'res_id': order.id,
                'view_id.id': target_form.id,
                'view_mode': 'form',
                'context': {'default_production_id': id},
                'target': 'new'
            }

        except requests.exceptions.ConnectTimeout:
            raise UserError(_("No se puede conectar a Sicbatch"))

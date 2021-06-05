import sys
from odoo import fields, models, api, _
from . import utils
from odoo.exceptions import UserError
import requests


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_done(self):
        res = super(StockPicking, self).action_done()
        config = self.env['config.connection'].search(
            [('company_id', '=', self.company_id.id)], limit=1)
        ws_url = config.server

        for record in self:
            lines = self.env['stock.move.line'].search([
                ('picking_id', '=', record.id)
            ])
            for line in lines:
                if line.product_id.product_tmpl_id.categ_id.send_sicbatch and line.location_dest_id.send_sicbatch \
                        and line.lot_id:

                    seq = config.sequence_lot.next_by_code(config.sequence_lot.code)
                    params = {
                        'name': 'spAlmacen_MateriaPrima_Lotes_Actualizar',
                        'param1': seq,
                        'param2': line.product_id.default_code,
                        'param3': line.product_id.name,
                        'param4': line.lot_id.name,
                        'param5': line.location_dest_id.id,
                        'param6': line.location_dest_id.name,
                        'param7': line.location_dest_id.tolva_id,
                        'param8': line.product_id.product_tmpl_id.is_micro_manual,
                        'param9': line.location_dest_id.tolva_etiqueta
                    }
                    response = requests.post(url=ws_url, json=params)
                    if response.status_code == 200:

                        utils.file_log(self, str(params), "spAlmacen_MateriaPrima_Lotes_Actualizar")
                        lot = self.env['stock.lot.sicbatch'].create({
                            'sequence_lot': seq,
                            'vendor_lot_id': line.lot_id.id,
                            'locator_to_id': line.location_dest_id.id
                        })
                    else:
                        raise UserError(_("No se puede conectar a sicbatch " + response.text))
        return res


class StockLotSicbatch(models.Model):
    _name = 'stock.lot.sicbatch'
    _description = 'Sicbatch lot control'

    sequence_lot = fields.Char()
    vendor_lot_id = fields.Many2one('stock.production.lot')
    locator_to_id = fields.Many2one('stock.location')


class StockMove(models.Model):
    _inherit = 'stock.move'

    sicbatch_lot = fields.Many2one('stock.lot.sicbatch')


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    @api.model
    def create(self, vals):
        move_id = self.env['stock.move'].search([('id', '=', vals['move_id'])])
        if move_id.sicbatch_lot:
            vals.update(
                {'location_id': move_id.sicbatch_lot.locator_to_id.id, 'lot_id': move_id.sicbatch_lot.vendor_lot_id.id})
        res = super(StockMoveLine, self).create(vals)
        return res

import sys

from odoo import fields, models, api, _

from . import sql_connection
from . import utils
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def action_done(self):
        res = super(StockPicking, self).action_done()
        for record in self:
            lines = self.env['stock.move.line'].search([
                ('picking_id', '=', record.id)
            ])
            for line in lines:
                if line.product_id.product_tmpl_id.categ_id.send_sicbatch and line.location_dest_id.send_sicbatch \
                        and line.lot_id:
                    try:
                        connect, config = sql_connection.sql_connect(self)
                        seq = config.sequence_lot.next_by_code(config.sequence_lot.code)
                        connection = True
                        cr = connect.cursor()
                        params = (
                            seq,
                            line.product_id.default_code,
                            line.product_id.name,
                            line.lot_id.name,
                            line.location_dest_id.id,
                            line.location_dest_id.name
                        )
                        sp = "spAlmacen_MateriaPrima_Lotes_Actualizar"
                        call_sp1 = cr.execute("{CALL " + sp + " (?,?,?,?,?,?)}", params)

                        utils.file_log(self, params, sp)
                        rows = cr.fetchone()
                        if not rows[0]:
                            raise UserError(sys.exc_info()[0])
                        lot = self.env['stock.lot.sicbatch'].create({
                            'sequence_lot': seq,
                            'vendor_lot_id': line.lot_id.id,
                            'locator_to_id': line.location_dest_id.id
                        })
                        cr.commit()
                    except:
                        raise ValueError(_(sys.exc_info()[0]))
                        if connection:
                            cr.rollback()

                    finally:
                        if connection:
                            cr.close()
                            connect.close()
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
            vals.update({'location_id': move_id.sicbatch_lot.locator_to_id.id, 'lot_id': move_id.sicbatch_lot.vendor_lot_id.id})
        res = super(StockMoveLine, self).create(vals)
        return res
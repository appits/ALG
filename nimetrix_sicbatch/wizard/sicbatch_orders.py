from odoo import fields, models, api, _

from ..models import utils
from ..models import sql_connection
from odoo.exceptions import UserError


class SicbatchOrders(models.TransientModel):
    _name = 'sicbatch.orders'
    _description = 'Sicbatch Orders'

    production_id = fields.Many2one('mrp.production')
    lines = fields.One2many('sicbatch.orders.lines', 'sicbatch_id')

    def process_order(self):
        for line in self.lines:
            if line.selected:
                try:
                    msg = 'Error en conexión'
                    connect, config = sql_connection.sql_connect(self.production_id)
                    connection = True
                    cr = connect.cursor()
                    call_sp1 = cr.execute("{CALL spResultOrden (?)}", line.order_id)
                    qty = 0.0
                    rows = cr.fetchall()
                    utils.send_log(self, line, rows, 'IP')

                    for row in rows:
                        if row == 0:
                            raise UserError(_(msg))

                        qty = row[4]
                        if not qty:
                            raise UserError(_(msg))
                        for rec in self.production_id.raw_workorder_line_ids:
                            if rec.product_id.default_code == row[2].strip():
                                rec.qty_done = row[3]

                    cr.commit()

                except:
                    if connection:
                        cr.rollback()
                    raise UserError(_('error al procesar datos de Sicbatch ' + str(msg)))

                finally:
                    if connection:
                        cr.close()
                        connect.close()


class SicbatchOrdersLines(models.TransientModel):
    _name = 'sicbatch.orders.lines'
    _description = 'Sicbatch Orders Lines'

    sicbatch_id = fields.Many2one('sicbatch.orders')
    order_id = fields.Integer()
    client_name = fields.Char()
    product_value = fields.Char()
    product_name = fields.Char()
    selected = fields.Boolean()



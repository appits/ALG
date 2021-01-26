import functools
import sys

from odoo import fields, models, api, _
from datetime import date
from odoo.exceptions import UserError

from . import sql_connection
from . import utils


class MrpWorkorder_Extension(models.Model):
    _inherit = 'mrp.workorder'

    check_start = fields.Boolean(default=False)
    check_end = fields.Boolean(default=False)
    check_sync_start = fields.Boolean(default=False)
    check_sync_end = fields.Boolean(default=False)
    sic_batch_logs = fields.One2many('sicbatch.log', 'work_order_id')

    @api.constrains('state')
    def set_check_operations(self):
        for record in self:
            config_head = record.env['config.connection'].search(
                [('company_id.id', '=', record.production_id.company_id.id),
                 ('lines_ids.routing_id.id', '=', record.production_id.routing_id.id)])
            config_line = record.env['config.connection.line'].search(
                [('routing_id', '=', record.production_id.routing_id.id),
                 ('config_head_id.id', '=', config_head.id)])
            for operation in config_line:
                if not record.check_start and not record.check_end:
                    if record.operation_id == operation.operation_start_id:
                        record.check_start = True
                    if record.operation_id == operation.operation_end_id:
                        record.check_end = True

        return

    @api.constrains('state')
    def set_check_sic_batch(self):
        for record in self:
            config_head = record.env['config.connection'].search(
                [('company_id.id', '=', record.production_id.company_id.id),
                 ('lines_ids.routing_id.id', '=', record.production_id.routing_id.id)])
            config_line = record.env['config.connection.line'].search(
                [('routing_id', '=', record.production_id.routing_id.id),
                 ('config_head_id.id', '=', config_head.id)])
            if record.state in ('ready', 'pro'):
                for operation in config_line:
                    if record.operation_id == operation.operation_start_id:
                        if not record.check_sync_start:
                            record.check_sync_start = True
        return

    '''
    def do_finish(self):
        for rec in self:
            #res = super(MrpWorkorder_Extension, rec).do_finish()
            for record in res:
                if record.check_sync_end:
                    raise UserError(
                        _('You must end the process using the end sicbatch button'))
            return res
'''
    def call_start_work_order(self):
        connection = False
        monitoring = ""
        for record in self:
            if not record.production_id.bom_id.code:
                raise UserError(_('Falta Código de referencia de la lista de materiales'))
            if not record.production_id.bom_id.product_tmpl_id.default_code:
                raise UserError(_('El Producto no posee código interno'))
            if not record.production_id.bom_id.product_tmpl_id.description:
                raise UserError(_('El Producto no posee Descripción'))
            try:
                monitoring = "Starting connection"
                cnxn, config = sql_connection.sql_connect(record)
                if not config.is_offline:
                    monitoring = "Send spReceta_Actualizar"
                    connection = True
                    cursor = cnxn.cursor()
                    params = (
                        record.production_id.bom_id.product_tmpl_id.default_code,
                        record.production_id.bom_id.product_tmpl_id.default_code,
                        record.production_id.bom_id.product_tmpl_id.name,
                        record.production_id.bom_id.product_tmpl_id.description)
                    call_sp1 = cursor.execute("{CALL spReceta_Actualizar (?,?,?,?)}", params)
                    row = cursor.fetchall()
                    utils.send_log(self, record, row, 'IP')

                    stock_move_line = record.env['stock.move'].search(
                        [('raw_material_production_id', '=', record.production_id.id)
                         ])
                    lines = 0
                    for line in stock_move_line:
                        if not line.product_id.product_tmpl_id.categ_id.send_sicbatch:
                            continue
                        lines = lines + 1
                        monitoring = line.product_id.product_tmpl_id.default_code + "_" + line.product_id.product_tmpl_id.name
                        cursor.execute("{CALL spDetalleReceta_Actualizar (?,?,?,?)}", (
                            record.production_id.bom_id.product_tmpl_id.default_code,
                            line.product_id.product_tmpl_id.default_code,
                            line.product_qty,
                            lines
                        ))

                    production = record.env['mrp.production'].search(
                        [('id', '=', record.production_id.id)])

                    partner_id = 0

                    if production.order_id.partner_id.parent_id:
                        partner_id = production.order_id.partner_id.parent_id
                    else:
                        partner_id = production.order_id.partner_id

                    batch = 1

                    if production.routing_id.capacity_batch > 0:
                        batch = int(round(production.product_qty / production.routing_id.capacity_batch))

                    params = (
                        production.id,
                        production.bom_id.product_tmpl_id.default_code,
                        partner_id.id,
                        partner_id.name,
                        production.product_qty,
                        batch,
                        production.bom_id.product_type
                    )
                    monitoring = "send spOrdenProduccion_Actualizar"
                    call_sp1 = cursor.execute("{CALL spOrdenProduccion_Actualizar  (?,?,?,?,?,?,?)}", params)
                    row = cursor.fetchall()
                    utils.send_log(self, record, row, 'IP')
                    record.button_start()
                    # record.action_continue()
                    cursor.commit()
                    record.check_sync_start = False
                    record.message_post(body="Process Sicbatch Started")
                    config_line = record.env['config.connection.line'].search(
                        [('operation_start_id', '=', record.operation_id.id)])
                    work_end = record.env['mrp.workorder'].search(
                        [('operation_id', '=', config_line.operation_end_id.id),
                         ('production_id', '=', record.production_id.id)])

                    work_end.check_sync_end = True
                    record.do_finish()
                    return
            except Exception as e:
                if connection:
                    cursor.rollback()
                    raise UserError(_('No se pudo enviar la orden a Sicbatch ' + monitoring+" error:"+str(e)))
            finally:
                if connection:
                    cursor.close()
                    cnxn.close()

    def call_end_work_order(self):
        connection = False
        count_lot = 0
        for record in self:
            if not record.finished_lot_id:
                record.action_generate_serial()
            try:
                msg = 'Error en conexión'
                connect, config = sql_connection.sql_connect(record)
                if not config.is_offline:
                    connection = True
                    cr = connect.cursor()
                    call_sp1 = cr.execute("{CALL spResultOrden (?,?)}", record.production_id.id,
                                          record.production_id.bom_id.product_type)
                    rows = cr.fetchall()
                    if len(rows) == 0:
                        raise UserError(_("No Procesado Aún"))

                    for rec in record.raw_workorder_line_ids:
                        record.button_start()
                        utils.send_log(self, record, rows, 'IP')

                        for row in rows:
                            if row[0] == 0:
                                raise UserError(_("No Procesado Aún"))
                            if rec.product_id.default_code != row[2].strip():
                                continue
                            qty = row[4]
                            if not qty:
                                raise UserError(_(msg))

                            lot = rec.env['stock.lot.sicbatch'].search([
                                ('sequence_lot', '=', str(row[6]).strip())
                            ])

                            if not lot:
                                raise UserError(_("No encontre el lote Sicbatch"))

                            if not rec.check_ids:
                                continue

                            rec.lot_id = lot.vendor_lot_id.id
                            rec.qty_done = row[3]
                            rec.qty_to_consume = row[3]
                            rec.qty_reserved = row[3]
                            rec.sicbatch_lot_id = lot.id
                            rec.move_id.location_id = lot.locator_to_id
                            rec.move_id.sicbatch_lot = lot.id
                            if rec.check_ids:
                                rec.check_ids.lot_id = lot.vendor_lot_id
                                record.action_next()

                    record.check_sync_end = False
                    record.do_finish()
                    cr.commit()

                    close_logs = record.env['sicbatch.log'].search([
                        ('production_id', '=', record.production_id.id)])
                    for log in close_logs:
                        log.status = 'DO'
            except Exception as e:
                if connection:
                    cr.rollback()
                    raise UserError(_('error al procesar datos de SicBatch ' + str(e)))

            finally:
                if connection:
                    cr.close()
                    connect.close()
        return


class MrpWorkOrderLine(models.Model):
    _inherit = 'mrp.workorder.line'

    sicbatch_lot_id = fields.Many2one('stock.lot.sicbatch')

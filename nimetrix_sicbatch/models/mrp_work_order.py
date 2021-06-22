import functools
import sys

import requests

from odoo import fields, models, api, _
from datetime import date
from odoo.exceptions import UserError

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
            try:
                monitoring = "Starting connection"
                config = get_config(self)
                if not config.is_offline:
                    url = config.server
                    monitoring = "Send spReceta_Actualizar"
                    connection = True

                    params = {
                        'name': 'spReceta_Actualizar',
                        'param1': record.production_id.bom_id.product_tmpl_id.default_code,
                        'param2': record.production_id.bom_id.product_tmpl_id.default_code,
                        'param3': record.production_id.bom_id.product_tmpl_id.name,
                        'param4': record.production_id.bom_id.product_tmpl_id.name
                    }
                    response = requests.post(url=url, json=params, timeout=8)

                    if response.status_code != 200:
                        raise UserError(_("No se puede conectar a sicbatch " + response.text))

                    utils.send_log(self, record, response.text, 'IP')
                    
                    lines = 0

                    for line in record.production_id.bom_id.bom_line_ids:
                        if not line.product_id.product_tmpl_id.categ_id.send_sicbatch:
                            continue
                        lines = lines + 1
                        monitoring = line.product_id.product_tmpl_id.default_code + "_" + line.product_id.product_tmpl_id.name
                        data = {
                            'name': 'spDetalleReceta_Actualizar',
                            'param1': record.production_id.bom_id.product_tmpl_id.default_code,
                            'param2': line.product_id.product_tmpl_id.default_code,
                            'param3': line.product_qty,
                            'param4': lines
                        }
                        response = requests.post(url=url, json=data)

                        if response.status_code != 200:
                            raise UserError(_("Cannot connect to sicbatch, error: " + response.text))
                            
                    production = record.env['mrp.production'].search(
                        [('id', '=', record.production_id.id)])

                    partner_id = 0

                    if production.order_id.partner_id.parent_id:
                        partner_id = production.order_id.partner_id.parent_id
                    else:
                        partner_id = production.order_id.partner_id

                    batch = 1

                    if production.bom_id.product_type == 'PT' and production.bom_id.capacity_batch > 0:
                        batch = int(round(production.product_qty / production.bom_id.capacity_batch))

                    params = {
                        'name': 'spOrdenProduccion_Actualizar',
                        'param1': production.id,
                        'param2': production.bom_id.product_tmpl_id.default_code,
                        'param3': partner_id.id if partner_id else production.company_id.partner_id.id,
                        'param4': partner_id.name if partner_id else production.company_id.partner_id.name,
                        'param5': production.product_qty,
                        'param6': batch,
                        'param7': production.bom_id.product_type
                    }
                    monitoring = "send spOrdenProduccion_Actualizar"
                    response = requests.post(url, json=params, timeout=8)
                    if response.status_code != 200:
                        raise UserError(_("Cannot connect to the sicbatch, error: " + response.text))

                    utils.send_log(self, record, response.text, 'IP')
                    record.button_start()
                    # record.action_continue()
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
                raise UserError(_('No se pudo enviar la orden a Sicbatch - Monitoreo ' + monitoring + " error:" + str(e)))

    def call_end_work_order(self):
        connection = False
        count_lot = 0
        for record in self:
            if not record.finished_lot_id:
                record.action_generate_serial()
            try:
                msg = 'Error en conexión'
                config = get_config(self)
                url = config.server
                if not config.is_offline:
                    connection = True

                    data = {
                        'name': 'spResultOrden',
                        'param1': record.production_id.id,
                        'param2': record.production_id.bom_id.product_type
                    }
                    response = requests.post(url=url, json=data)

                    if response.status_code != 200:
                        raise UserError(_("Cannot connect to sicbatch, error: "+response.text))

                    if len(response.json()) == 0:
                        raise UserError(_("No Procesado Aún"))

                    for rec in record.raw_workorder_line_ids:
                        record.button_start()
                        utils.send_log(self, record, response.text, 'IP')

                        for resp in response.json():

                            if resp['Result'] == 0:
                                raise UserError(_('No procesado aún'))

                            if rec.product_id.default_code != resp['BoMid'].strip():
                                continue
                            qty = float(resp['Consumed'])
                            if not qty:
                                raise UserError(_(msg))

                            lot = rec.env['stock.lot.sicbatch'].search([
                                ('sequence_lot', '=', resp['LoteId'].strip())
                            ])

                            if not lot:
                                raise UserError(_("No encontre el lote Sicbatch "+resp['LoteId'].strip()))

                            if not rec.check_ids:
                                continue

                            rec.lot_id = lot.vendor_lot_id.id
                            rec.qty_done = qty
                            rec.qty_to_consume = qty
                            rec.qty_reserved = qty
                            rec.sicbatch_lot_id = lot.id
                            rec.move_id.location_id = lot.locator_to_id
                            rec.move_id.sicbatch_lot = lot.id
                            rec.move_id.sicbatch_lot = lot.id
                            if rec.check_ids:
                                rec.check_ids.lot_id = lot.vendor_lot_id
                                record.action_next()

                    record.check_sync_end = False
                    record.do_finish()

                    data = {
                        'name': 'spCloseProduction',
                        'param1': record.production_id.id,
                        'param2': record.production_id.bom_id.product_type
                    }

                    res = requests.post(url=url, json=data, timeout=4)

                    if res.status_code != 200:
                        raise UserError(_("No se pudo cerrar la orden de producción"))

                    close_logs = record.env['sicbatch.log'].search([
                        ('production_id', '=', record.production_id.id)])
                    for log in close_logs:
                        log.status = 'DO'
            except Exception as e:
                raise UserError(_('error al procesar datos de SicBatch ' + str(e)))
        return


def get_config(self):
    config = self.env['config.connection'].search(
        [('company_id', '=', self.company_id.id)])
    return config


class MrpWorkOrderLine(models.Model):
    _inherit = 'mrp.workorder.line'

    sicbatch_lot_id = fields.Many2one('stock.lot.sicbatch')

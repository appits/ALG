# -*- coding: utf-8 -*-
###############################################################################
#
#    INGEINT SA.
#    Copyright (C) 2020 INGEINT SA-(<http://www.ingeint.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from odoo import api, fields, models


class Picking(models.Model):
    _inherit = 'stock.picking'

    transport = fields.Char()
    car_plate = fields.Char()
    date_driver = fields.Char()
    identification_driver = fields.Char()
    total_qty = fields.Float()
    type_transaction = fields.Char()
    transaction_main = fields.Boolean(default=False, copy=False)
    import_form_num = fields.Char()
    import_dossier = fields.Char()
    import_date = fields.Date()
    purchase_id = fields.Many2one('purchase.order')
    invoice_reference = fields.Char()
    note_reference = fields.Char()
    guide_ids = fields.One2many('office.guide', 'picking_id')
    guide_cancel_ids = fields.One2many('cancel.guide', 'picking_id')

    # Functions Constrains

    @api.constrains('picking_type_id')
    def get_picking_type(self):
        if not self.type_transaction:
            self.type_transaction = self.picking_type_id.code

    @api.constrains('sale_id')
    def set_transaction_main(self):
        if self.sale_id:
            if self.sale_id.warehouse_id.lot_stock_id.id == self.location_id.id and self.location_dest_id.usage == 'customer':
                self.transaction_main = True
        elif self.type_transaction == 'incoming':
            if self.location_id.usage == 'supplier':
                self.transaction_main = True

    @api.constrains('state')
    def get_total_qty(self):
        for record in self:
            if record.state == 'done':
                total = 0
                for line in record.move_line_ids_without_package:
                    total += line.qty_done
                record.total_qty = total

    @api.constrains('origin')
    def get_purchase_order(self):
        if self.type_transaction == 'incoming':
            record = self.env['purchase.order'].search([('name', '=', self.origin)])
            self.purchase_id = record.id
            if record:
                for record_line in record:
                    self.transport = record_line.transport
                    self.car_plate = record_line.car_plate
                    self.date_driver = record_line.date_driver
                    self.identification_driver = record_line.identification_driver
                    self.import_form_num = record_line.import_form_num
                    self.import_dossier = record_line.import_dossier
                    self.import_date = record_line.import_date
        elif self.type_transaction == 'outgoing':
            record = self.env['sale.order'].search([('name', '=', self.origin)])
            if record:
                for record_line in record:
                    self.transport = record_line.transport
                    self.car_plate = record_line.car_plate
                    self.date_driver = record_line.date_driver
                    self.identification_driver = record_line.identification_driver

    # Other Functions

    def generate_report(self):
        guide_ids = self.env['office.guide'].search([('picking_id.id', '=', self.id), ('processed', '=', True)])
        if not guide_ids:
            guide_ids = self.env['office.guide'].create({'picking_id': self.id, 'processed': True})
            guide_ids.generate_number()

        data = self
        return self.env.ref('reports_lanta.reporte_guia_despacho').report_action(data)

    def cancel_sequence(self):
        guide_ids = self.env['office.guide'].search([('picking_id.id', '=', self.id), ('processed', '=', True)])
        for record in guide_ids:
            record.processed = False

    def generate_report_note(self):
        data = self
        return self.env.ref('reports_lanta.reporte_nota_carga').report_action(data)

    def generate_report_reception(self):
        data = self
        return self.env.ref('reports_lanta.reporte_informe_recepcion').report_action(data)


class OfficeGuide(models.Model):
    _name = 'office.guide'

    ctrl_number = fields.Char(copy=False)
    picking_id = fields.Many2one('stock.picking')
    processed = fields.Boolean()

    def generate_number(self):
        correlative = self.env['office.guide'].search(
            [('ctrl_number', '=', self.ctrl_number), ('id', '!=', self.id)])
        for det_corr in correlative:
            if det_corr.ctrl_number:
                raise UserError(_(' El valor :%s ya se uso en otro documento') % det_corr.ctrl_number)
        self.ctrl_number = self.get_invoice_ctrl_number_unique()

    def get_invoice_ctrl_number_unique(self):

        self.ensure_one()
        SEQUENCE_CODE = 'l10n_ve_nro_control_unico_formato_libre'
        company_id = 1
        IrSequence = self.env['ir.sequence'].with_context(force_company=1)
        name = IrSequence.next_by_code(SEQUENCE_CODE)

        if not name:
            IrSequence.sudo().create({
                'prefix': '00-',
                'name': 'Localización Venezolana nro control Unico Factura Forma Libre %s' % 1,
                'code': SEQUENCE_CODE,
                'implementation': 'no_gap',
                'padding': 4,
                'number_increment': 1,
                'company_id': 1,
            })
            name = IrSequence.next_by_code(SEQUENCE_CODE)
        return name


class CancelSequence(models.TransientModel):
    _name = 'cancel.guide'

    picking_id = fields.Many2one('stock.picking')

    def cancel_sequence(self):
        self.picking_id.cancel_sequence()

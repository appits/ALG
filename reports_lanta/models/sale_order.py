from odoo import fields, models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    transport = fields.Char()
    car_plate = fields.Char()
    date_driver = fields.Char()
    identification_driver = fields.Char()


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    dose_kgton = fields.Float()

    @api.onchange('product_id')
    def set_dose_kgton(self):
        for record in self:
            if record.product_id:
                if record.product_id.product_tmpl_id.dosis_kgton:
                    record.dose_kgton = record.product_id.product_tmpl_id.dosis_kgton

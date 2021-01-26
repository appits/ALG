from odoo import fields, models, api


class Purchase(models.Model):
    _inherit = 'purchase.order'

    transport = fields.Char()
    car_plate = fields.Char()
    date_driver = fields.Char()
    identification_driver = fields.Char()
    import_form_num = fields.Char()
    import_dossier = fields.Char()
    import_date = fields.Date()

    def action_view_invoice(self):
        result = super(Purchase, self).action_view_invoice()
        recep = self.env['stock.picking'].search([('purchase_id.id', '=', self.id)])
        for record in recep:
            result['context']['default_transport'] = record.transport
            result['context']['default_car_plate'] = record.car_plate
            result['context']['default_date_driver'] = record.date_driver
            result['context']['default_identification_driver'] = record.identification_driver
            result['context']['default_import_form_num'] = record.import_form_num
            result['context']['default_import_dossier'] = record.import_dossier
            result['context']['default_import_date'] = record.import_date
        return result


class PurchaseLine(models.Model):
    _inherit = 'purchase.order.line'

    product_packaging_id = fields.Many2one('product.packaging')

from odoo import fields, models, api


class StockLot (models.Model):
    _inherit = 'stock.production.lot'

    sicbatch_lot_id = fields.Integer()

    



from odoo import fields, models, api


class StockInventory(models.TransientModel):
    _name = 'stock.print'
    _description = 'Parameters print Reports'

    inventory_id = fields.Many2one('stock.inventory')
    inventory_line_id = fields.Many2one('stock.inventory.line')
    last = fields.Boolean(default=False)
    code = fields.Char()
    nro = fields.Integer()
    nro_total = fields.Integer()
    product_id = fields.Many2one('product.product')
    lot_id = fields.Many2one('stock.production.lot')
    date = fields.Date()
    location_id = fields.Many2one('stock.location')
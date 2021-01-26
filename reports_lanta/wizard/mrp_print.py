from odoo import fields, models, api


class MrpPrint(models.TransientModel):
    _name = 'mrp.print'
    _description = 'Parameters print Reports'

    mrp_id = fields.Many2one('mrp.production')
    bom_id = fields.Many2one('mrp.bom')
    nro = fields.Integer()
    product_packaging_id = fields.Many2one('product.packaging')
    product_id = fields.Many2one('product.product')
    lot_id = fields.Many2one('stock.production.lot')
    date = fields.Date()
    date_f = fields.Date()
    routing_id = fields.Many2one('mrp.routing')

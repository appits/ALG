from odoo import fields, models, api


class Location (models.Model):
    _inherit = 'stock.location'

    send_sicbatch = fields.Boolean()
    tolva_id = fields.Integer()
    tolva_etiqueta = fields.Char()


    



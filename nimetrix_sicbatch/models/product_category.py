from odoo import fields, models, api


class ProductCategory (models.Model):
    _inherit = 'product.category'

    send_sicbatch = fields.Boolean()
    



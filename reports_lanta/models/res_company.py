from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    image_production_1920 = fields.Image("Variant Image", max_width=1920, max_height=1920)
    image_production_2_1920 = fields.Image("Variant Image 2", max_width=1920, max_height=1920)


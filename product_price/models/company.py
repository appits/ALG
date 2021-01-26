from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"


    days = fields.Integer(string='Days')

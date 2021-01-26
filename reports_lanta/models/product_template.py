from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    dosis_kgton = fields.Float()
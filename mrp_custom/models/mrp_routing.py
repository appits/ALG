from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class MrpRouting(models.Model):
    _inherit = 'mrp.routing'

    capacity_batch = fields.Float(default=0)

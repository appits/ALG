from odoo import fields, models, api


class RoutingExtends(models.Model):
    _inherit = 'mrp.routing'

    connexion_line_r = fields.One2many('config.connection.line', 'routing_id')


class RoutingLineExtends(models.Model):
    _inherit = 'mrp.routing.workcenter'

    check_start = fields.Boolean(default=False)
    check_end = fields.Boolean(default=False)

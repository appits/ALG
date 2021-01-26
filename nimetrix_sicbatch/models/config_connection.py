from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

from . import sql_connection


class ConfigConnection(models.Model):
    _name = 'config.connection'
    _description = 'Config Connection'

    name = fields.Char()
    company_id = fields.Many2one('res.company', string="Company", required="True")
    server = fields.Char(string="Server", required="True")
    database = fields.Char(string="Data Base", required="True")
    db_user = fields.Char(string="Username", required="True")
    db_password = fields.Char(string="Password", required="True")
    lines_ids = fields.One2many('config.connection.line', 'config_head_id')
    sequence = fields.Many2one('ir.sequence')
    sequence_manual = fields.Many2one('ir.sequence')
    sequence_lot = fields.Many2one('ir.sequence')
    is_offline = fields.Boolean()

    def test_connection(self):
        try:
            msg = "Not Connected"
            connected = False
            connect = sql_connection.test_connect(self)
            connected = True
            cr = connect.cursor()
            test = cr.execute("SELECT @@VERSION").fetchall()
            msg = test
            raise UserWarning(_(msg))
        except:
            raise UserError(_(msg))
        finally:
            if connected:
                cr.close()
                connect.close()

    @api.constrains('company_id')
    def set_name_default(self):
        self.name = self.company_id.name


class ConfigConnectionLine(models.Model):
    _name = 'config.connection.line'
    _description = 'Config Connection Line'

    config_head_id = fields.Many2one('config.connection', 'Config Connexion')
    routing_id = fields.Many2one('mrp.routing', string="Routing", required="True")
    operation_start_id = fields.Many2one('mrp.routing.workcenter', domain="[('routing_id', '=', routing_id)""]",
                                         string="Operation Start", required="True")
    operation_end_id = fields.Many2one('mrp.routing.workcenter', domain="[('routing_id', '=', routing_id)""]",
                                       string="Operation End", required="True")

    id = fields.Integer()

    @api.onchange('routing_id')
    def clean_operations(self):
        self.operation_start_id = False
        self.operation_end_id = False

    @api.constrains('operation_start_id', 'operation_end_id', 'routing_id')
    def validate_duplicate_operations(self):
        for line in self:
            if line.operation_start_id == line.operation_end_id:
                raise UserError(_('You are duplicating operations on the line'))

    @api.constrains('routing_id')
    def validate_duplicate_routing(self):
        for row in self:
            routing = [x.id for x in self.search(
                [('config_head_id', '=', row.config_head_id.id), ('routing_id', '=', row.routing_id.id)])]
            routing.remove(row.id)
            if len(routing) >= 1:
                raise UserError(_('The routing on the line exist'))

    @api.constrains('operation_start_id', 'operation_end_id')
    def set_start_end(self):
        for record in self:
            record.set_check(True, self.routing_id.id)

    @api.model
    def unlink(self):
        for record in self:
            record.set_check(False, self.routing_id.id)
        return super(ConfigConnectionLine, self).unlink()

    def set_check(self, boolean, routing_id):
        operation = self.env['mrp.routing.workcenter'].search([('routing_id', '=', routing_id)])

        for clean in operation:
            clean.check_start = False
            clean.check_end = False

        for rec in operation:
            if rec.id == self.operation_start_id.id:
                rec.check_start = boolean
            if rec.id == self.operation_end_id.id:
                rec.check_end = boolean

    @api.constrains('operation_start_id', 'operation_end_id')
    def onchange_operation(self):
        for lines in self:
            mrp_production = lines.env['mrp.production'].search(
                [('routing_id.id', '=', lines.routing_id.id), ('state', '!=', 'done')])
            for production in mrp_production:
                mrp_work_order = production.env['mrp.workorder'].search(
                    [('production_id.id', '=', production.id), ('state', '!=', 'done')])
                for record_clean in mrp_work_order:
                    if record_clean.check_end or record_clean.check_start:
                        if record_clean.state != 'progress':
                            record_clean.check_end = False
                            record_clean.check_start = False
                    else:
                        raise UserError(
                            _('you cannot change a work in progress center, the center is: %s') % record_clean.name)
                for record_mark in mrp_work_order:
                    if not record_mark.check_start and not record_mark.check_end:
                        if record_mark.operation_id == lines.operation_start_id:
                            record_mark.check_start = True
                        if record_mark.operation_id == lines.operation_end_id:
                            record_mark.check_end = True

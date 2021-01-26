from odoo import fields, models, api


class SicBatchLog (models.Model):
    _name = 'sicbatch.log'
    _description = 'SicBatch Log'

    api_call = fields.Char()
    script = fields.Text()
    response = fields.Text()
    create_date = fields.Datetime()
    write_date = fields.Datetime()
    status = fields.Selection([
        ('IP', 'In Progress'),
        ('DO', 'Done')
    ])
    work_order_id = fields.Many2one('mrp.workorder')
    create_uid = fields.Many2one('res.users')
    write_uid = fields.Many2one('res.users')
    production_id = fields.Many2one('mrp.production')

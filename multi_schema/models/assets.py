from odoo import fields, models, api
from . import utils


class Assets(models.Model):
    _inherit = 'account.asset'

    operation_currency = fields.Many2one('res.currency')
    rate = fields.Float()
    currencies_asset_ids = fields.Many2many('currencies.asset')

    @api.onchange('operation_currency')
    def get_default_rate(self):
        for record in self:
            if self.operation_currency:
                self.rate = utils.get_rate(record, self.acquisition_date)

    @api.constrains('state')
    def set_value_of_currencies(self):
        currencies = []
        for record in self:
            if record.state == 'open' and not record.currencies_asset_ids:
                schemas = record.env['acct.schema'].search([
                    ('company_id', '=', record.company_id.id)
                ])

                for schema in schemas:
                    date, rate = utils.get_schema_rate(schema, record.acquisition_date)
                    currencies_ids = record.env['currencies.asset'].create({
                        'date_currency': date,
                        'rate': rate,
                        'schema_id': schema.id
                    })
                    currencies += [currencies_ids.id]
        self.currencies_asset_ids = currencies



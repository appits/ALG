from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    currency_from_id = fields.Many2one('res.currency')
    currency_to_id = fields.Many2one('res.currency')
    percent_max_variation = fields.Float()
    currency_rate_from = fields.Float()
    date_currency_from = fields.Datetime()
    currency_rate_to = fields.Float()
    date_currency_to = fields.Datetime()
    difference = fields.Float()
    percent_variation = fields.Float()
    calculate_vals = fields.Boolean(compute='calculation_rates', default=False)
    control_bom = fields.Boolean(default=False, copy=False)

    def calculation_rates(self):
        self['calculate_vals'] = True
        if self.currency_from_id and self.currency_to_id:
            date_from, rate_from = self.get_rate(self.currency_from_id.id)
            date_to, rate_to = self.get_rate(self.currency_to_id.id)
            if date_from and rate_from and date_to and rate_to:
                difference = rate_to - rate_from
                percent = (difference / rate_to) * 100
                self['currency_rate_from'] = rate_from
                self['date_currency_from'] = date_from
                self['currency_rate_to'] = rate_to
                self['date_currency_to'] = date_to
                self['difference'] = difference
                self['percent_variation'] = percent
            else:
                self['currency_rate_from'] = 0
                self['date_currency_from'] = False
                self['currency_rate_to'] = 0
                self['date_currency_to'] = False
                self['difference'] = 0
                self['percent_variation'] = 0

    def get_rate(self, currency_id):
        self.env.cr.execute("SELECT max(rate_date), rate "
                            "FROM multi_currency_rate "
                            "WHERE currency_id = %s "
                            "GROUP BY rate_date, rate "
                            "ORDER BY rate_date desc ",
                            [currency_id])

        value = self._cr.fetchone()

        if not value:
            date = False
            value = 0
            return date, value

        return value[0], value[1]

    @api.onchange('currency_from_id', 'currency_to_id')
    def onchange_currencies(self):
        if self.currency_from_id and self.currency_to_id:
            self.calculation_rates()

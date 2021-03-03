from odoo import fields, models, api
from datetime import date
from datetime import datetime

def get_rate(self, date):
    self.env.cr.execute("SELECT max(rate_date), rate "
                        "FROM multi_currency_rate "
                        "WHERE currency_id = %s "
                        "AND rate_date <= %s "
                        "GROUP BY rate_date, rate "
                        "ORDER BY rate_date desc ",
                        [self.operation_currency.id, date])

    value = self._cr.fetchone()

    if not value:
        return

    return value[1]


def get_schema_rate(self, date):
    self.env.cr.execute("SELECT max(rate_date), rate "
                        "FROM multi_currency_rate "
                        "WHERE currency_id = %s "
                        "AND rate_date <= %s "
                        "GROUP BY rate_date, rate "
                        "ORDER BY rate_date desc ",
                        [self.currency_id.id, date])

    value = self._cr.fetchone()

    if not value:
        return self.create_date, 0

    return value[0], value[1]


def get_invoice_rate(self):
    dt = datetime.combine(self.date, datetime.max.time())
    self.env.cr.execute("SELECT max(rate_date), rate "
                        "FROM multi_currency_rate "
                        "WHERE currency_id = %s "
                        "AND rate_date <= %s "
                        "GROUP BY rate_date, rate "
                        "ORDER BY rate_date desc ",
                        [self.currency_from_id.id, dt])

    value = self._cr.fetchone()

    if not value:
        return self.create_date, 0

    return value[0], value[1]

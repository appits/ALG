from odoo import fields, models, api
from datetime import date
from datetime import timedelta


class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    is_price_manual = fields.Boolean(default=False, copy=False)
    price_rate_convert = fields.Float()

    @api.model
    def create(self, vals):
        res = super(SupplierInfo, self).create(vals)
        currency = self.env.company.currency_from_id
        if not res.is_price_manual:
            res.date_start = date.today()
            res.date_end = date.today() + timedelta(days=15)

        if currency:
            if res.currency_id.id != currency.id:
                date_currency, rate = self.env.company.get_rate(currency.id)
                if date and rate:
                    res.price_rate_convert = round(res.price / rate, 2)
            else:
                res.price_rate_convert = res.price
        return res

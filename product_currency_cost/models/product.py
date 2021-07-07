# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def get_default_second_currency(self):
        currency = self.env.ref('base.USD')
        return currency


    standard_price_second_currency = fields.Monetary(compute='_compute_standard_price_second_currency', 
        currency_field='second_currency', string='Coste en US$')
    second_currency = fields.Many2one('res.currency', default=get_default_second_currency)

    @api.depends_context('force_company')
    @api.depends('standard_price')
    def _compute_standard_price_second_currency(self):
        today = fields.Date.today()
        company_currency = self.env.user.company_id.currency_id.with_context(date=today)
        for product in self:
            price = company_currency.compute(product.standard_price, product.second_currency)
            product.standard_price_second_currency = price







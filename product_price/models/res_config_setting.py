# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class SaleConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'


    days = fields.Integer(string='Days', default=lambda self: self.env.user.company_id.days)

    
    def get_values(self):
        res = super(SaleConfigSettings, self).get_values()
        res.update(
            days = self.env.user.company_id.days,
        )
        return res

    def set_values(self):
        super(SaleConfigSettings, self).set_values()
        self.env.user.company_id.days = self.days

# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    is_depreciated = fields.Boolean(default=False)
    first_depreciation_date = fields.Date(required=False)

    def validate(self):
        self.write({'state': 'open'})
        if self.is_depreciated is False:
            super().validate()
    
    @api.depends('value_residual', 'salvage_value', 'children_ids.book_value', 'is_depreciated')
    def _compute_book_value(self):
        super()._compute_book_value()
        for asset in self:
            if asset.is_depreciated:
                asset.book_value = 0
                asset.value_residual = 0
    
    @api.onchange('original_value')
    def _onchange_value(self):
        if self.is_depreciated:
            self.value_residual = 0
        else:
            super()._onchange_value()

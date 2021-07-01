# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    is_depreciated = fields.Boolean(default=False)
    first_depreciation_date = fields.Date(required=False)
    already_depreciated_amount_import = fields.Monetary(readonly=True, states={'draft': [('readonly', False)]})
    depreciation_number_import = fields.Integer(readonly=True, states={'draft': [('readonly', False)]})
    depreciation_accumulate = fields.Monetary(compute='_compute_depreciation_accumulate')

    @api.depends(
        'already_depreciated_amount_import', 
        'depreciation_move_ids',
        'depreciation_move_ids.state',
        'is_depreciated'
    )
    def _compute_depreciation_accumulate(self):
        for asset in self:
            if asset.is_depreciated:
                asset.depreciation_accumulate = asset.original_value
            else:
                move_balance = sum(asset.depreciation_move_ids.filtered(lambda r:
                    r.state == 'posted' and not r.reversal_move_id).mapped('amount_total'))
                asset.depreciation_accumulate = asset.already_depreciated_amount_import + move_balance
    
    @api.depends('value_residual', 'salvage_value', 'children_ids.book_value', 'is_depreciated')
    def _compute_book_value(self):
        super()._compute_book_value()
        for asset in self:
            if asset.is_depreciated:
                asset.book_value = 0
                asset.gross_increase_value = 0
    
    @api.onchange('salvage_value')
    def _onchange_salvage_value(self):
        self._compute_values()
    
    @api.onchange('depreciation_accumulate')
    def _onchange_depreciation_accumulate(self):
        self._compute_values()
    
    def _compute_values(self):
        for asset in self:
            if self.is_depreciated:
                asset.salvage_value = 0
                asset.value_residual = 0
            else:
                asset.value_residual = asset.original_value - asset.depreciation_accumulate - asset.salvage_value

    def validate(self):
        self.write({'state': 'open'})
        if self.is_depreciated is False:
            super().validate()

    def _recompute_board(self, depreciation_number, starting_sequence, amount_to_depreciate, 
        depreciation_date, already_depreciated_amount, amount_change_ids):
        if self.depreciation_number_import:
            starting_sequence += self.depreciation_number_import
        
        return super()._recompute_board(depreciation_number, starting_sequence, amount_to_depreciate,
            depreciation_date, already_depreciated_amount, amount_change_ids)
    
    @api.model
    def create(self, vals):
        asset = super().create(vals)
        if 'original_value' in vals:
            asset._compute_values()
        return asset


    def write(self, vals):
        res = super().write(vals)
        if 'original_value' in vals:
            self._compute_values()
        return res

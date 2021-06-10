# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def reverse_moves(self):
        if self.refund_method != 'refund':
            self = self.with_context(create_account_tax_for_moves=True)
        res = super(AccountMoveReversal, self).reverse_moves()
        return res


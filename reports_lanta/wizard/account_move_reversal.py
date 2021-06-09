# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'


    def reverse_moves(self):
        res = super().reverse_moves()
        move_id = res.get('res_id') or res.get('domain')[0][2][0]
        if self.refund_method == 'cancel':
            self.move_tax_full_refund(move_id)        
        return res
    
    @api.model
    def move_tax_full_refund(self, move_id):
        move = self.env['account.move'].browse(move_id)
        if move.type in ('out_invoice', 'in_invoice', 'in_refund', 'out_refund', 'out_receipt', 'in_receipt'):
            for line in move.invoice_line_ids:
                if line.tax_ids:

                    for tax in line.tax_ids:
                        tax_total = (line.price_subtotal * tax.amount) / 100
                        move.create_account_move_tax_transient(move.id, tax.id, line.price_subtotal, tax.amount, tax_total)

            self._cr.execute(
                ' select move_id, tax_id, sum(base_tax) as base_tax , tax_percent, sum(tax_total) '
                ' from account_move_tax_transient '
                ' where move_id = %s '
                ' group by move_id, tax_id, tax_percent',
                [move.id])
            value = self._cr.fetchall()
            if value:
                for sql_value in value:
                    move_id = sql_value[0]
                    tax_id = sql_value[1]
                    base_tax = sql_value[2]
                    tax_percent = sql_value[3]
                    tax_total = sql_value[4]
                    move.create_account_move_tax(move_id, tax_id, base_tax, tax_percent, tax_total)
        return True

from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    account_tax_ids = fields.One2many('account.move.tax', 'move_id')

    def action_post(self):
        res = super(AccountMove, self).action_post()
        if self.type in ('out_invoice', 'in_invoice', 'in_refund', 'out_refund', 'out_receipt', 'in_receipt'):
            for lines in self.invoice_line_ids:
                if lines.tax_ids:
                    for tax in lines.tax_ids:
                        tax_total = (lines.price_subtotal * tax.amount) / 100
                        self.create_account_move_tax_transient(self.id, tax.id, lines.price_subtotal, tax.amount, tax_total)

            self._cr.execute(
                ' select move_id, tax_id, sum(base_tax) as base_tax , tax_percent, sum(tax_total) '
                ' from account_move_tax_transient '
                ' where move_id = %s '
                ' group by move_id, tax_id, tax_percent',
                [self.id])
            value = self._cr.fetchall()

            if value:
                for sql_value in value:
                    move_id = sql_value[0]
                    tax_id = sql_value[1]
                    base_tax = sql_value[2]
                    tax_percent = sql_value[3]
                    tax_total = sql_value[4]
                    self.create_account_move_tax(move_id, tax_id, base_tax, tax_percent, tax_total)

            return res

    def create_account_move_tax(self, move_id, tax_id, base_tax, tax_percent, tax_total):
        taxes = self.env['account.move.tax'].create({'move_id': move_id,
                                                     'tax_id': tax_id,
                                                     'base_tax': base_tax,
                                                     'tax_percent': tax_percent,
                                                     'tax_total': tax_total
                                                     })
        return taxes

    def create_account_move_tax_transient(self, move_id, tax_id, base_tax, tax_percent, tax_total):
        taxes_transient = self.env['account.move.tax.transient'].create({'move_id': move_id,
                                                                         'tax_id': tax_id,
                                                                         'base_tax': base_tax,
                                                                         'tax_percent': tax_percent,
                                                                         'tax_total': tax_total
                                                                         })
        return taxes_transient

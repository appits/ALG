# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class WizNroctrl(models.TransientModel):
    _inherit = 'wiz.nroctrl'

    def set_noctrl(self):
        """ Change control number of the invoice
        """
        account_move = self.env['account.move']
        invoice = account_move.browse(self._context.get('active_id', False))

        if not self.sure:
            raise UserError("Confirme que desea hacer esto marcando la casilla opción")
        n_ctrl = self.name

        if not invoice.maq_fiscal_p:
            nro_ctrl_count = account_move.search_count([('nro_ctrl', '=', n_ctrl)])
            if nro_ctrl_count:
                raise UserError("El Numero de Control ya Existe")
            
        invoice.nro_ctrl = n_ctrl
        return True
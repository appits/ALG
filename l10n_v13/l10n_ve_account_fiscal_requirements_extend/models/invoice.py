# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Invoice(models.Model):
    _inherit = 'account.move'

    @api.onchange('maq_fiscal_p')
    def onchange_maquina_fiscal(self):
        if self.maq_fiscal_p:
            self.nro_ctrl = '0'
        else:
            self.nro_ctrl = ''
    
    @api.constrains('maq_fiscal_p')
    def _check_maq_fiscal_p(self):
        for invoice in self:
            if invoice.maq_fiscal_p and not invoice.nro_ctrl:
                raise ValidationError('Debe ingresar un numero de control.')


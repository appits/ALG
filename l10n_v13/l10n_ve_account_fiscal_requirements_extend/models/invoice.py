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
            super().onchange_maquina_fiscal()
    
    @api.constrains('maq_fiscal_p')
    def _check_maq_fiscal_p(self):
        for invoice in self:
            types = ('out_refund', 'in_refund')
            if invoice.maq_fiscal_p and not invoice.nro_ctrl and invoice.type not in types:
                raise ValidationError('Debe ingresar un numero de control.')
    
    @api.model
    def create(self, values):
        invoice = super().create(values)

        if invoice.maq_fiscal_p and not invoice.nro_ctrl:
            invoice.nro_ctrl = '0'
        
        return invoice


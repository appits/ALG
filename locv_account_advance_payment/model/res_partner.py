# coding: utf-8
###########################################################################

from odoo import models, fields, api


class res_partner(models.Model):
    '''Se crea dos campos para agregar a la ficha del cliente y proveedor las cuentas
     contables de anticipo a cliente y proveedor'''

    _inherit = 'res.partner'
    es_cliente = fields.Boolean(string='Es un cliente', default=False,
                                help="Chequea si el usuario es un cliente")
    es_proveedor = fields.Boolean(string='Es un proveedor', default=False,
                                  help="Chequeca si el usuario es Proveedor")
    tipo_usuario = fields.Selection(string='Cliente o proveedor',
                                    selection=[('cliente', 'Cliente'), ('proveedor', 'Proveedor'), ('ambos', 'Ambos')],
                                     inverse='_write_cliente_type')
    account_advance_payment_purchase_id = fields.Many2one('account.account','Cuenta de Anticipos de Compras')
    account_advance_payment_sales_id = fields.Many2one('account.account','Cuenta de Anticipos de Ventas')
    journal_advanced_id = fields.Many2one('account.journal','Diario de Anticipos')

    # @api.depends('es_cliente')
    # def _compute_cliente_type(self):
    #     if self.es_cliente == True and self.es_proveedor == True:
    #         for partner in self:
    #             partner.tipo_usuario = 'ambos'
    #     else:
    #         if self.es_cliente == True:
    #             for partner in self:
    #                 partner.tipo_usuario = 'cliente'
    #         if self.es_proveedor == True:
    #             for partner in self:
    #                 partner.tipo_usuario = 'proveedor'

    def _write_cliente_type(self):
        for partner in self:
            if partner.tipo_usuario == 'ambos':
                partner.es_cliente = True
                partner.es_proveedor = True
            else:
                partner.es_cliente = partner.tipo_usuario == 'cliente'
                partner.es_proveedor = partner.tipo_usuario == 'proveedor'

    @api.onchange('tipo_usuario')
    def onchange_company_type(self):
        if self.tipo_usuario == 'ambos':
            self.es_cliente = True
            self.es_proveedor = True
        else:
            self.es_cliente = (self.tipo_usuario == 'cliente')
            self.es_proveedor = (self.tipo_usuario == 'proveedor')
# -*- coding: UTF-8 -*-
#    type of the change:  Created
#    Comments: Creacion de generacion de codigo para clientes y proveedores (depends for res_partner)



from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import re



class RespartnerRif(models.Model):
    _inherit = 'res.partner'

    def write(self, vals):
        res = {}
        if vals.get('vat'):
            res = self.validate_rif_er(vals.get('vat', False))
            if not res:
                raise exceptions.except_orm(('Advertencia!'), (
                    'El rif tiene el formato incorrecto. Ej: V-012345678, E-012345678, J-012345678 o G-012345678. Por favor verifique el formato y si posee los 9 digitos como se indica en el Ej. e intente de nuevo'))
            # ~ if not self.validate_rif_duplicate(vals.get('vat', False)):
                # ~ print(self.validate_rif_duplicate(vals.get('vat', False)),"errors")
                # ~ raise exceptions.except_orm(('Advertencia!'),
                                            # ~ (
                                                # ~ u'El cliente o proveedor ya se encuentra registrado con el rif: %s y se encuentra activo') % (
                                                # ~ vals.get('vat', False)))
        if vals.get('email'):
            res = self.validate_email_addrs(vals.get('email'), 'email')
            if not res:
                raise exceptions.except_orm(('Advertencia!'), (
                    'El email es incorrecto. Ej: cuenta@dominio.xxx. Por favor intente de nuevo'))
        res = super(RespartnerRif, self).write(vals)
        return res



    @api.model
    def create(self, vals):
        res = {}
        if vals.get('vat'):
            res = self.validate_rif_er(vals.get('vat'))
            if not res:
                raise exceptions.except_orm(('Advertencia!'), (
                    'El rif tiene el formato incorrecto. Ej: V-012345678, E-012345678, J-012345678 o G-012345678. Por favor verifique el formato y si posee los 9 digitos como se indica en el Ej. e intente de nuevo'))

        if vals.get('email'):
            res = self.validate_email_addrs(vals.get('email'), 'email')
            if not res:
                raise exceptions.except_orm(('Advertencia!'), (
                    'El email es incorrecto. Ej: cuenta@dominio.xxx. Por favor intente de nuevo'))
        res = super(RespartnerRif, self).create(vals)
        return res


    def validate_rif_er(self, field_value):
        res = {}

        rif_obj = re.compile(r"^[V|E|J|G]+[-][\d]{9}", re.X)
        if rif_obj.search(field_value.upper()):
            if len(field_value) == 11:
                res = {
                    'vat':field_value
                }
            else:
                res ={}
        return res


    @api.constrains('vat')
    def check_vatnumber(self):
        for record in self:
            obj = self.search([('vat','=',record.vat),('id','!=',record.id)])
            if obj:
                print(obj,"rif")
                raise ValidationError(_('''El cliente o proveedor ya se encuentra registrado con el rif: %s y se encuentra activo''' % (record.vat)))


    def validate_email_addrs(self, email, field):
        res = {}

        mail_obj = re.compile(r"""
                \b             # comienzo de delimitador de palabra
                [\w.%+-]       # usuario: Cualquier caracter alfanumerico mas los signos (.%+-)
                +@             # seguido de @
                [\w.-]         # dominio: Cualquier caracter alfanumerico mas los signos (.-)
                +\.            # seguido de .
                [a-zA-Z]{2,3}  # dominio de alto nivel: 2 a 6 letras en minúsculas o mayúsculas.
                \b             # fin de delimitador de palabra
                """, re.X)     # bandera de compilacion X: habilita la modo verborrágico, el cual permite organizar
                               # el patrón de búsqueda de una forma que sea más sencilla de entender y leer.
        if mail_obj.search(email):
            res = {
                field:email
            }
        return res

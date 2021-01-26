# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models


class Libreria(models.Model):
    _name = "library.book"
    name=fields.Char(string='Titulo',required=True)
    data_release=fields.Date('Release date')
    autor_id=fields.Many2many('res.partner',string='Autores')


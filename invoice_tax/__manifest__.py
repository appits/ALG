# -*- coding: utf-8 -*-
{
    'name': "Invoice Tax",

    'summary': """
        Generate records parallel to the invoice for each tax applied""",

    'description': """
        Generate records parallel to the invoice for each tax applied
    """,

    'author': "Jorge Piñero",
    'website': "http://www.ingeint.com",

    'category': 'account',
    'version': '0.1',

    'depends': ['base', 'account'],

    'data': [
        'security/ir.model.access.csv',
        #'views/account_move.xml'
    ],
    'demo': [
    ],
}

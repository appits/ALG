# -*- coding: utf-8 -*-
{
    'name': "My Libreria",

    'summary': """ejercicio nro 1""",

    'description': """
      crear un modulo.
    """,
    'version': '2.0',
    'author': 'Darrell Sojo. Ing 1',
    'category': 'Tools',

    # any module necessary for this one to work correctly
    'version':'12.0.1',
    'depends': ['base'],

    # always loaded
    'data': [        
        'vista_view.xml',
        'security/groups.xml',
        'security/ir.model.access.csv'
    ],
    'application': True,
}

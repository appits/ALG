# -*- coding: utf-8 -*-
{
    'name': "Lanta de Venezuela - SicBatch",

    'description': """
       Extension module for connection of web services and generation of productions
    """,

    'author': "Orlando Curieles, Jorge Pinero",
    'website': "http://www.nimetrix.com",

    'version': '0.1',

    'depends': ['base',
                'mrp',
                'mrp_workorder',
                'sale',
                'stock'
                ],
    'data': [
        'security/ir.model.access.csv',
        'views/config_connection.xml',
        'views/menu.xml',
        'views/mrp_work_order.xml',
        'views/routing_work_center.xml',
        'views/transactions_logs.xml',
        'views/mrp_production.xml',
        'views/product_category.xml',
        'views/location.xml',
        'views/mrp_bom.xml',
        'wizard/sicbatch_orders.xml'
    ],
}

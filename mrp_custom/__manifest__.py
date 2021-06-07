# -*- coding: utf-8 -*-
{
    'name': "Manufacturing custom",

    'summary': """
      Custom Manufacturing""",

    'description': """
        Custom Manufacturing
    """,

    'author': "Ingeint / Jorge Pinero",
    'website': "http://www.ingeint.com",

    'category': 'mrp',
    'version': '0.1',

    'depends': ['base', 'mrp', 'sale', 'sale_management', 'nimetrix_sicbatch', 'reports_lanta'],

    'data': [
        # 'security/ir.model.access.csv',
        'views/products.xml',
        'views/mrp_production.xml',
        'views/stock_location.xml',
        'views/sale_order.xml',
        'views/stock_picking.xml',
        'views/mrp_bom.xml',
        'wizard/picking_warning.xml',
        'wizard/picking_list.xml',
        'wizard/plan_production_by_orders.xml',
    ],
}

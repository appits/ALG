# -*- coding: utf-8 -*-
{
    'name': "Reportes Lanta",

    'description': """
        Personalizacion  de reportes
    """,
    'author': "Ingeint",
    'website': "http://www.ingeint.com",
    'category': 'reports',
    'version': '0.1',
    'depends': ['base', 'stock', 'sale', 'purchase', 'account', 'mrp', 'invoice_tax'],
    'data': [
        'views/cancel_sequence.xml',
        'security/report_group.xml',
        'security/ir.model.access.csv',
        'views/picking.xml',
        'views/purchase_order.xml',
        'views/sale_order.xml',
        'views/account_move.xml',
        'views/stock_inventory.xml',
        'views/mrp_bom.xml',
        'views/mrp_production.xml',
        'views/res_company.xml',
        'views/partner.xml',
        'views/product_template.xml',
        'reports/guia_despacho.xml',
        'reports/informe_recepcion.xml',
        'reports/nota_carga.xml',
        'reports/factura_lanta.xml',
        'reports/invetory_labels.xml',
        'reports/mrp_production.xml',
        'reports/nc_lanta.xml',
        'reports/nd_lanta.xml'
    ],
}

# -*- coding: utf-8 -*-
{
    'name': "Quotation lanta",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Jorge Pinero",
    'website': "http://www.ingeint.com",

    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'sale_management', 'contacts', 'nimetrix_sicbatch', 'mrp', 'reports_lanta'],

    # always loaded
    'data': [
        'security/quotation_group.xml',
        'security/ir.model.access.csv',
        'views/res_company.xml',
        'views/res_partner.xml',
        'views/quotation.xml',
        'views/supplierInfo.xml',
        'views/product_template.xml',
        'views/mrp_bom.xml'
    ],
}

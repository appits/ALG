# -*- coding: utf-8 -*-
{
    'name': "multi-schema",

    'summary': """
        Multi-Schema accounting """,

    'description': """
        Multi-Currency
        Multi - Accounting
        Multi - Assets information
        Multi - Inventory
    """,

    'author': "INGEINT SA",
    'website': "https://www.ingeint.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base_setup', 'product', 'analytic', 'portal', 'digest', 'account', 'base', 'account_asset'],
    # always loaded
    'data': [
        'security/Multi_schema_group.xml',
        'security/ir.model.access.csv',
        'views/invoice.xml',
        'views/currency_rate.xml',
        'views/assets.xml',
        'views/gl_journal.xml',
        'views/products.xml',
        'views/fact_acct.xml',
        'wizard/report_fact_acct.xml',
        'wizard/report_financial.xml',
        'wizard/profit_and_loss.xml',
        'wizard/aged_receivable.xml',
        'wizard/aged_payable.xml',
        'wizard/Inventory_valuation.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

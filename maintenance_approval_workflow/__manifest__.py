# -*- coding: utf-8 -*-
{
    'name': "Maintenance Request Approval Workflow",
    'version': '2.2',
    'price': 19.0,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'category': 'Operations/Maintenance',
    'summary': """Equipment Maintenance Request Approval Workflow""",
    'description': """
Maintenance Approval Workflow
Maintenance Request Approval Workflow
Maintenance Request
Equipment Maintenance Request Approval Workflow

    """,
    'author': "Probuse Consulting Service Pvt. Ltd.",
    'website': 'www.probuse.com',
    'images': ['static/description/approval_request.jpg'],
    'live_test_url': 'https://youtu.be/l-sGV0T-884',
    'depends': ['base', 'maintenance'],
    'data': [
        'views/maintenance_stage_view.xml',
        'data/approval_workflow.xml',
    ],
    'installable': True,
    'application': False,
    
}

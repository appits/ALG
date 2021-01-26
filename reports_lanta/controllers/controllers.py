# -*- coding: utf-8 -*-
# from odoo import http


# class ReportNimetrix(http.Controller):
#     @http.route('/report_nimetrix/report_nimetrix/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/report_nimetrix/report_nimetrix/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('report_nimetrix.listing', {
#             'root': '/report_nimetrix/report_nimetrix',
#             'objects': http.request.env['report_nimetrix.report_nimetrix'].search([]),
#         })

#     @http.route('/report_nimetrix/report_nimetrix/objects/<model("report_nimetrix.report_nimetrix"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('report_nimetrix.object', {
#             'object': obj
#         })

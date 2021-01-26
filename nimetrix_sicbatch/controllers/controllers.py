# -*- coding: utf-8 -*-
from odoo import http


class NimetrixSync(http.Controller):
    @http.route('/api/test', auth='public')
    def index(self, **kw):
        return "Hello, world"

#     @http.route('/nimetrix-sync-batch/nimetrix-sync-batch/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('nimetrix-sync-batch.listing', {
#             'root': '/nimetrix-sync-batch/nimetrix-sync-batch',
#             'objects': http.request.env['nimetrix-sync-batch.nimetrix-sync-batch'].search([]),
#         })

#     @http.route('/nimetrix-sync-batch/nimetrix-sync-batch/objects/<model("nimetrix-sync-batch.nimetrix-sync-batch"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('nimetrix-sync-batch.object', {
#             'object': obj
#         })

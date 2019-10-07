# -*- coding: utf-8 -*-
from odoo import http

# class Geoemeter(http.Controller):
#     @http.route('/geoemeter/geoemeter/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/geoemeter/geoemeter/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('geoemeter.listing', {
#             'root': '/geoemeter/geoemeter',
#             'objects': http.request.env['geoemeter.geoemeter'].search([]),
#         })

#     @http.route('/geoemeter/geoemeter/objects/<model("geoemeter.geoemeter"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('geoemeter.object', {
#             'object': obj
#         })
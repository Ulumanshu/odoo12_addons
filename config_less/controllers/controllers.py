# -*- coding: utf-8 -*-
from odoo import http

# class ConfigCless(http.Controller):
#     @http.route('/config_cless/config_cless/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/config_cless/config_cless/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('config_cless.listing', {
#             'root': '/config_cless/config_cless',
#             'objects': http.request.env['config_cless.config_cless'].search([]),
#         })

#     @http.route('/config_cless/config_cless/objects/<model("config_cless.config_cless"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('config_cless.object', {
#             'object': obj
#         })
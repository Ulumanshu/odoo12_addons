# -*- coding: utf-8 -*-
from odoo import http

# class Zuvinimas(http.Controller):
#     @http.route('/zuvinimas/zuvinimas/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/zuvinimas/zuvinimas/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('zuvinimas.listing', {
#             'root': '/zuvinimas/zuvinimas',
#             'objects': http.request.env['zuvinimas.zuvinimas'].search([]),
#         })

#     @http.route('/zuvinimas/zuvinimas/objects/<model("zuvinimas.zuvinimas"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('zuvinimas.object', {
#             'object': obj
#         })
from odoo import models, fields, api

def prynt(print_me):
    import sys
    print(print_me)
    sys.stdout.flush()

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _name = 'product.template'
    
    country_of_origin_id = fields.Many2one('res.country', 'Country Of Origin')


from odoo import models, fields, api

def prynt(print_me):
    import sys
    print(print_me)
    sys.stdout.flush()

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _name = 'product.template'
    
    colour = fields.Char('Colour')
    
    @api.onchange('categ_id')
    def default_values(self):
        def cat_find(category):
            if category.name:
                if category.name == 'Zafu cushions':
                    return True
                else:
                    return cat_find(category.parent_id)
            else:
                return False
        cond = cat_find(self.categ_id)
        if self.categ_id and cond:
            self.responsible_id = self.env['res.users'].search([('name', '=', 'Petra')])
            self.route_ids = self.env['stock.location.route'].search([('name', '=', 'Manufacture')])
            self.type = 'product'
            self.uom_id = self.env['uom.uom'].search([('name', '=', 'Unit(s)')])
            self.taxes_id = None
            self.purchase_ok = False
            self.list_price = 80
            self.produce_delay = 1
            self.sale_delay = 5
            self.weight = 3
            self.volume = 0.02
            
   
            

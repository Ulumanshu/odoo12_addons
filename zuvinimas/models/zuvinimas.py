# -*- coding: utf-8 -*-

from odoo import models, fields, api

class zuvinimas(models.Model):
    _name = 'zuvinimas.main'

    
#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100

class zuvinimas_regions(models.Model):
     _name = 'zuvinimas.regions'
     
     name = fields.Char("Region")
     water_body_ids = fields.One2many("zuvinimas.lakes", "region_id", "Belonging Water Bodies")


class zuvinimas_lakes(models.Model):
     _name = 'zuvinimas.lakes'
     
     name = fields.Char("Name Of Water Body")
     region_id = fields.Many2one("zuvinimas.regions", "Waterbody Region")
     

class zuvinimas_realeases(models.Model):
     _name = 'zuvinimas.releases'
     
     date = fields.Date("Date Of Release")
     species_id = fields.Many2one("zuvinimas.species", "Fish Species")
     age_group_id = fields.Many2one("zuvinimas.species.age", "Fish Species Age Group")
     water_body_id = fields.Many2one("zuvinimas.lakes", "Concerned Waterbody")
     quantity = fields.Integer("Release Quantity")
     
    
class zuvinimas_species(models.Model):
     _name = 'zuvinimas.species'
     
     name = fields.Char("Species Name")
     
     
class zuvinimas_species_age(models.Model):
     _name = 'zuvinimas.species.age'
     
     name = fields.Char("Species Age Group")
     age = fields.Char("Age Group Scientific Marking")
     
     

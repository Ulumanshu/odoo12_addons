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
     
    name = fields.Char("Region", required=True, translate=True)
    image = fields.Binary("Region Image", store=True)
    water_body_count = fields.Integer('Waterbody Count')
    water_body_ids = fields.One2many("zuvinimas.lakes", "region_id", "Belonging Water Bodies")
    
    @api.multi
    def write(self, vals):
        res = super(zuvinimas_regions, self).write(vals)
        if vals.get('water_body_ids'):
            self.water_body_count = len(self.water_body_ids)
        return res
        
    @api.depends('water_body_ids')
    def body_counter(self):
        for rec in self:
            rec.water_body_count = len(rec.water_body_ids)
            

class zuvinimas_lakes(models.Model):
    _name = 'zuvinimas.lakes'

    name = fields.Char("Name Of Water Body", required=True, translate=True)
    image = fields.Binary("Lake Image", store=True)
    release_count = fields.Integer('Release Count')
    area = fields.Float("Area In Hectares")
    region_id = fields.Many2one("zuvinimas.regions", "Waterbody Region", required=True)
    releases_ids = fields.One2many('zuvinimas.releases', "water_body_id", "Releases Into Waterbody")
    
    @api.multi
    def write(self, vals):
        res = super(zuvinimas_lakes, self).write(vals)
        if vals.get('releases_ids'):
            self.release_count = len(self.releases_ids)
        return res
    
    @api.depends('releases_ids')
    def release_counter(self):
        for rec in self:
            rec.release_count = len(rec.releases_ids)
        

class zuvinimas_realeases(models.Model):
    _name = 'zuvinimas.releases'

    date = fields.Date("Date Of Release", required=True)
    species_id = fields.Many2one("zuvinimas.species", "Fish Species", required=True)
    age_group_id = fields.Many2one("zuvinimas.species.age", "Fish Species Age Group", required=True)
    water_body_id = fields.Many2one("zuvinimas.lakes", "Concerned Waterbody", required=True)
    quantity = fields.Float("Release Quantity", required=True)
    
    
class zuvinimas_species(models.Model):
    _name = 'zuvinimas.species'

    name = fields.Char("Species Name", required=True, translate=True)
    image = fields.Binary("Species Image", store=True)
    latin_name = fields.Char("Latin Name")
    releases_ids = fields.One2many('zuvinimas.releases', "species_id", "Releases Of Species")
    
    
class zuvinimas_species_age(models.Model):
    _name = 'zuvinimas.species.age'

    name = fields.Char("Species Age Group", required=True, translate=True)
    age = fields.Char("Age Group Scientific Marking")
     
     

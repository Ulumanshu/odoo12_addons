# -*- coding: utf-8 -*-

from odoo import models, fields, api
import os
import json

def prynt(print_me):
    import sys
    print(print_me)
    sys.stdout.flush()


class zuvinimas(models.Model):
    _name = 'zuvinimas.main'

#    @api.depends('releases_ids')
#    def _count_species(self):
#        for rec in self:
#            rset_species = self.env['zuvinimas.species']
#            for release in self.releases_ids:
#                rset_species |= release.species_id
#            rec.species_ids = rset_species

#    @api.multi
#    def write(self, vals):
#        res = super(zuvinimas_regions, self).write(vals)
#        if vals.get('water_body_ids'):
#            self.water_body_count = len(self.water_body_ids)
#        return res

#    @api.multi
#    def write(self, vals):
#        res = super(zuvinimas_lakes, self).write(vals)
#        if vals.get('releases_ids'):
#            self.release_count = len(self.releases_ids)
#        return res


class zuvinimas_regions(models.Model):
    _name = 'zuvinimas.regions'
    
    @api.depends('water_body_ids')
    def _count_lakes(self):
        for rec in self:
            rec.water_body_count = len(rec.water_body_ids)
            area = 0.00
            for body in rec.water_body_ids:
                area += body.area
            rec.total_wb_area = area
     
    name = fields.Char("Region", required=True, translate=True)
    region_notes = fields.Text("Region Notes")
    image = fields.Binary("Region Image", store=True)
    water_body_count = fields.Integer('Waterbody Count', compute="_count_lakes")
    total_wb_area = fields.Float("Total Waterbody Area", compute="_count_lakes")
    water_body_ids = fields.One2many(
        "zuvinimas.lakes",
        "region_id",
        "Belonging Water Bodies"
    )
    

class zuvinimas_lakes(models.Model):
    _name = 'zuvinimas.lakes'
    
    @api.depends('releases_ids')
    def _count_releases(self):
        for rec in self:
            rec.release_count = len(rec.releases_ids)
            rset_species = rec.env['zuvinimas.species']
            for release in rec.releases_ids:
                rset_species |= release.species_id
            rec.species_ids = rset_species
            
    @api.depends('name', 'region_id.name', "g_query")
    def _get_default_map_image(self):
        api_key = ''
        dir_path = os.path.dirname(os.path.realpath(__file__))
        dir_path_level = os.path.dirname(os.path.dirname(os.path.dirname(dir_path)))
        filename = os.path.join(dir_path_level, 'etc/api_keys.json')
        with open(filename) as f:
            api_key = json.load(f).get('maps')
        for rec in self:
            if not rec.g_query:
                region = rec.region_id and rec.region_id.name and "+in+%s" % rec.region_id.name or ''
                query = "in+Lithuania+ezeras%s" % rec.name
                query += region
            else:
                query = rec.g_query
            url = 'https://www.google.com/maps/embed/v1/search?key=%s&q=%s' % (api_key, query)
            template = self.env.ref('zuvinimas.lake_location')
            rec.image_html = template.render({ 'url' : url })
    
    name = fields.Char("Name Of Water Body", required=True, translate=True)
    image_html = fields.Html(
        "Lake Image",
        compute=_get_default_map_image,
         sanitize=False,
         strip_style=False
    )
    g_query = fields.Char("Query For Google Maps")
    correct_map = fields.Boolean("Correct Map")
    release_count = fields.Integer('Release Count', compute="_count_releases")
    area = fields.Float("Area In Hectares")
    lake_notes = fields.Text("Waterbody Notes")
    region_id = fields.Many2one("zuvinimas.regions", "Waterbody Region", required=True)
    releases_ids = fields.One2many(
        'zuvinimas.releases',
        "water_body_id",
        "Releases Into Waterbody"
    )
    species_ids = fields.Many2many(
        'zuvinimas.species',
        'zuvinimas_lakes_species_rel',
        'lake_id',
        'species_id',
        compute="_count_releases"
    )
    

class zuvinimas_realeases(models.Model):
    _name = 'zuvinimas.releases'
    _rec_name = 'date'
     
    @api.model
    def _getfilter(self, species=None):
        domain = []
        if species:
            domain.append('|')
            domain.append(('species_id', '=', species.id))
        domain.append(('base_age_group', '=', True))
        return domain
    
    date = fields.Date("Date Of Release", required=True)
    species_id = fields.Many2one("zuvinimas.species", "Fish Species", required=True)
    age_group_id = fields.Many2one(
        "zuvinimas.species.age",
        "Fish Species Age Group",
        required=True,
        domain=_getfilter
    )
    water_body_id = fields.Many2one(
        "zuvinimas.lakes",
        "Concerned Waterbody",
        required=True
    )
    region_id = fields.Many2one(
        "zuvinimas.regions",
        "Waterbody Region",
        related='water_body_id.region_id'
    )
    quantity = fields.Float("Release Quantity", required=True)
    
    @api.onchange('species_id')
    def _correct_age_groups(self):
        for rec in self:
            res = {}
            rec.age_group_id = False
            domain = self._getfilter(self.species_id)
            res['domain'] = {'age_group_id': domain}
            return res
    
    
class zuvinimas_species(models.Model):
    _name = 'zuvinimas.species'
    
    @api.depends('releases_ids')
    def _count_releases(self):
        for rec in self:
            rec.release_count = len(rec.releases_ids)
            rec.domain_location_id = self.env.context.get('domain_location_id') or None
            res = 0.00
            for release in rec.releases_ids:
                if rec.domain_location_id:
                    if release.water_body_id != rec.domain_location_id:
                        continue
                res += release.quantity
            rec.release_quantity_count = res
            
    def _filter_by_age(self):
        for req in self:
            age_groups = self.env['zuvinimas.species.age'].search(
                ['|', ('species_id', '=', self.id), ('base_age_group', '=', True)]
            )
            req.age_group_ids = age_groups
    
    name = fields.Char("Species Name", required=True, translate=True)
    species_notes = fields.Text("Species Notes")
    image = fields.Binary("Species Image", store=True)
    latin_name = fields.Char("Latin Name")
    release_count = fields.Integer('Release Count', compute="_count_releases")
    release_quantity_count = fields.Float(
        'Released Quantity',
        compute="_count_releases"
    )
    releases_ids = fields.One2many(
        'zuvinimas.releases',
        "species_id",
        "Releases Of Species"
    )
    age_group_ids = fields.One2many(
        'zuvinimas.species.age',
        'species_id',
        string="Age Groups Of The Species",
        compute="_filter_by_age"
    )
    domain_location_id = fields.Many2one(
        'zuvinimas.lakes',
        'Computed Quantity Location',
        compute="_count_releases"
    )
    
    
class zuvinimas_species_age(models.Model):
    _name = 'zuvinimas.species.age'

    name = fields.Char("Species Age Group", required=True, translate=True)
    age = fields.Char("Age Group Scientific Marking")
    base_age_group = fields.Boolean("Species Inspecific Age Group")
    species_id = fields.Many2one("zuvinimas.species", "Fish Species")
    releases_ids = fields.One2many(
        'zuvinimas.releases',
        "age_group_id",
        "Releases Of Age Group"
    )
     
    @api.onchange('base_age_group', 'species_id')
    def _group_depends(self):
        for rec in self:
            if rec.base_age_group:
                rec.species_id = False
            
            

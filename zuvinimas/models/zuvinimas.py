# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import datetime
import os
import json

def prynt(print_me):
    import sys
    print(print_me)
    sys.stdout.flush()


class zuvinimas(models.Model):
    _name = 'zuvinimas.main'

    @api.model
    def create(self, vals):
        res = super(zuvinimas, self).create(vals)
        period_obj = self.env['zuvinimas.main.period']
        period_species_obj = self.env['zuvinimas.main.period.species']
        spc_ag_obj = self.env['zuvinimas.main.period.species.age_groups']
        releases_obj = self.env['zuvinimas.releases']
        releases_ids = releases_obj.search([])
        sorted_rels_ids = releases_ids.sorted(key=lambda r: r.date)
        if len(sorted_rels_ids) > 2:
            min_date = sorted_rels_ids[0].date.replace(month=1, day=1)
            max_date = sorted_rels_ids[-1].date.replace(month=12, day=31)
            one_day = relativedelta(days=1)
            one_year = relativedelta(years=1)
            focus = min_date
            while focus < max_date:
                periods_releases_ids = sorted_rels_ids.filtered(
                    lambda r: r.date >= focus and r.date <= focus + one_year - one_day
                )
                period = period_obj.create({
                    'name': focus.strftime("%Y"),
                    'main_id': res.id
                })
                period.period_release_qty = sum(periods_releases_ids.mapped(lambda r: r.quantity))
                species_list = list(set(periods_releases_ids.mapped('species_id.name')))
                for sp in species_list:
                    species = period_species_obj.create({
                        'name': sp,
                        'period_id': period.id
                    })
                    species_releases = periods_releases_ids.filtered(
                        lambda r: r.species_id.name == sp
                    )
                    species.total_release_qty = sum(species_releases.mapped(lambda r: r.quantity))
                    species_age_group_list = list(set(species_releases.mapped('age_group_id.age')))
                    for group in species_age_group_list:
                        age_group = spc_ag_obj.create({
                            'sci_name': group,
                            'period_species_id': species.id
                        })
                        age_group_releases = species_releases.filtered(
                            lambda r: r.age_group_id.age == group
                        )
                        age_group.age_group_release_qty = sum(
                            age_group_releases.mapped(lambda r: r.quantity)
                        )
                        species.p_species_age_group_ids += age_group
                    period.period_species_ids += species
                res.period_ids += period
                focus += one_year
        
        return res
    
    @api.model
    def get_default_timeframe_name(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M")
    
    name = fields.Char("Timeframe", default=get_default_timeframe_name)
    period_ids = fields.One2many(
        'zuvinimas.main.period',
        'main_id',
        'Years With Planned Releases',
        readonly=True
    )
    

class zuvinimas_main_period(models.Model):
    _name = 'zuvinimas.main.period'
    
    name = fields.Char("Year")
    main_id = fields.Many2one('zuvinimas.main', 'Timeframe', ondelete='cascade')
    period_release_qty = fields.Float('Total Period Release Quantity')
    period_species_ids = fields.One2many(
        'zuvinimas.main.period.species',
        'period_id',
        'Species Released This Year'
    )
    
    
class zuvinimas_main__period_species(models.Model):
    _name = 'zuvinimas.main.period.species'

    name = fields.Char("Period Species")
    period_id = fields.Many2one('zuvinimas.main.period', 'Current Year', ondelete='cascade')
    total_release_qty = fields.Float('Total Quantity Released')
    p_species_age_group_ids = fields.One2many(
        'zuvinimas.main.period.species.age_groups',
        'period_species_id',
        'Age Group Releases This Year'
    )
    

class zuvinimas_main__period_species_age_groups(models.Model):
    _name = 'zuvinimas.main.period.species.age_groups'
    _rec_name = "sci_name"
    
    sci_name = fields.Char("Scientific Name")
    period_species_id = fields.Many2one(
        'zuvinimas.main.period.species',
        'Period Species',
        ondelete='cascade'
    )
    age_group_release_qty = fields.Float('Total Age Group Release Quantity')
    

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
    
    date = fields.Date("Date Of Release", required=True)
    species_id = fields.Many2one("zuvinimas.species", "Fish Species", required=True)
    age_group_id = fields.Many2one(
        "zuvinimas.species.age",
        "Fish Species Age Group",
        required=True,
        domain="['|', ('species_id', '=', species_id), ('base_age_group', '=', True)]"
    )
    water_body_id = fields.Many2one("zuvinimas.lakes", "Concerned Waterbody")
    region_id = fields.Many2one(
        "zuvinimas.regions",
        "Waterbody Region",
        related='water_body_id.region_id'
    )
    quantity = fields.Float("Release Quantity", required=True)
    
    @api.onchange('species_id')
    def _correct_age_groups(self):
        for rec in self:
            species_age_groups = self.env['zuvinimas.species.age'].search(
                ['|', ('species_id', '=', rec.species_id.id), ('base_age_group', '=', True)]
            )
            if rec.age_group_id not in species_age_groups:
                rec.age_group_id = False


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
            
            

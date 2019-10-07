# -*- coding: utf-8 -*-

from odoo import models, fields, api
import sys
import re

def prynt(print_me):
    print(print_me)
    sys.stdout.flush()

class geometer_settings(models.Model):
    _name = 'geometer.settings'
    
    name = fields.Char('Geometer Settings')
    api_key = fields.Char('Api Key')
    api_url1 = fields.Char('Api Url')
    center_lat = fields.Float("Default Centerpoint Latitude", digits=(32, 15))
    center_lng = fields.Float("Default Centerpoint Longitude", digits=(32, 15))
    zoom = fields.Integer('Default Zoom')

class geometer(models.Model):
    _name = 'geometer.geometer'

    name = fields.Char('Mainframe')
    location_ids = fields.One2many(
        'geometer.location',
        "mainframe_id",
        "Collection Locations"
    )
    note = fields.Text("Short Description")
    settings_id = fields.Many2one(
        'geometer.settings',
        'Settings Object',
        default=lambda self: self.env.ref('geometer.main_settings_obj').id
    )


class geometer_location(models.Model):
    _name = 'geometer.location'

    @api.model
    def get_default_lat(self):
        main_settings = self.env.ref('geometer.main_settings_obj')
        return main_settings.center_lat
    
    @api.model
    def get_default_lng(self):
        main_settings = self.env.ref('geometer.main_settings_obj')
        return main_settings.center_lng
    
    @api.model
    def get_default_zoom(self):
        main_settings = self.env.ref('geometer.main_settings_obj')
        return main_settings.zoom
    
    @api.depends('marker_ids')
    def _onch_marker_ids(self):
        for rec in self:
            rec.total_distance = sum([m.distance for m in rec.marker_ids]) / 1000
    
    name = fields.Char('Location Name')
    mainframe_id = fields.Many2one('geometer.geometer', 'Collection') 
    center_lat = fields.Float(
        "Default Centerpoint Latitude", digits=(32, 15), default=get_default_lat
    )
    center_lng = fields.Float(
        "Default Centerpoint Longitude", digits=(32, 15), default=get_default_lng
    )
    zoom = fields.Integer('Default Zoom', default=get_default_zoom)
    marker_ids = fields.One2many('geometer.location.marker', 'location_id', 'Map Markers')
    total_distance = fields.Float(
        ' Total Distance Between Markers', digits=(32, 4), compute="_onch_marker_ids"
    )


class geometer_location_marker(models.Model):
    _name = 'geometer.location.marker'

    name = fields.Char('Marker Name')
    sequence = fields.Integer('Marker Sequence')
    lat = fields.Float("Marker Latitude", digits=(32, 15))
    lng = fields.Float("Marker Longitude", digits=(32, 15))
    distance = fields.Float('Distance To Previous Meters', digits=(32, 4))
    distance_start = fields.Float('Distance To Startpoint Kilometers', digits=(32, 4))
    location_id = fields.Many2one('geometer.location', 'Location')
    
    @api.model
    def load_markers(self, loc_id):
        location_obj = self.env['geometer.location']
        res = []
        loc = location_obj.browse(loc_id)
        if loc.marker_ids:
            res = [
                {'lat': m.lat, 'lng': m.lng, 'name': m.name, 'sequence': m.sequence}
                for m in loc.marker_ids
            ]
        return res

    @api.model
    def create_markers(self, new_markers_list):
        location_obj = self.env['geometer.location']
        marker_obj = self.env['geometer.location.marker']
        res = {}
        form_view_URI = ''
        model = False
        if new_markers_list:
            loc_id = new_markers_list.get('1').get('location_id')
            loc_rec = location_obj.browse(loc_id)
            old_markers = loc_rec.marker_ids
            old_markers.unlink()
            for key, new_marker in new_markers_list.items():
                prynt(new_marker)
                if key == 'own_ctx':
                    form_view_URI = new_marker['uri']
                    loc_rec.write({
                        'center_lat': new_marker['center']['lat'],
                        'center_lng': new_marker['center']['lng'],
                        'zoom': new_marker['zoom']
                    })
                    continue
                marker_vals = {
                    'name': new_marker.get('name'),
                    'sequence': new_marker.get('sequence'),
                    'lat': new_marker.get('lat'),
                    'lng': new_marker.get('lng'),
                    'distance': new_marker.get('distance'),
                    'distance_start': new_marker.get('distance_start'),
                    'location_id': new_marker.get('location_id')
                }
                marker_obj.create(marker_vals)
            res = {
                "type": "ir.actions.client",
                "tag": "reload",
                'view_mode': 'form',
                'res_id': loc_id,
                'res_model': 'goemeter.location',
                'view_type': 'form',
                "view_id": self.env.ref("geometer.geometer_location_form").id,
                'target': 'current',
            }
            if form_view_URI:
                model = re.search(r"(model=[^\&]+)", str(form_view_URI)) and \
                    re.search(r"(model=[^\&]+)", str(form_view_URI)).group(1) or False
                model = model[6:]
                if model == 'geometer.geometer':
                    self.browse
                    res['target'] = 'new'
                    res['res_model'] = 'goemeter.geometer'
                    res['res_id'] = loc_rec.mainframe_id.id
                    res['view_id'] = self.env.ref("geometer.geometer_form").id
       
        return res
        


odoo.define('geometer.geoManager', [
        'web.ajax',
        'web.Widget',
        'web.dom_ready',
        'web.FormController',
        'web.widget_registry'
    ], function (require) {
    "use strict";
    
    var ajax = require('web.ajax');
    var widgetRegistry = require('web.widget_registry');
    var dom_Ready = require('web.dom_ready');
    var Widget = require('web.Widget');
    

    var geoManager =  Widget.extend({
        template: 'geometer.geomap_widget_template',
        init: function (parent, options) {
            this._super(parent);
            this.loc_obj = options.data;
            this.map = false;
            this.center = {lat: this.loc_obj.center_lat, lng: this.loc_obj.center_lng};
            this.zoom = this.loc_obj.zoom;
            this.loadedMarkers = [];
            this.markersArray = [];
            this.polylineData = [];
            this.polylines = [];
            this.bounds = {};
            this.labels = Array.from(new Array(100), (x,i) => (i + 1).toString());
            this.labelIndex = 0;
            this.location = false;
            this.dist_in_km = 0.0;
        },
        start: function () {
            setTimeout(() => {
                this.map = new google.maps.Map(this.$el[2], {zoom: this.zoom, center: this.center});
                this.loadMarkers();
                google.maps.event.addListener(this.map, 'click', (event) => {
                    this.location = event.latLng;
                    this.addMarker();
                });
                $('#read_geomap').click((ev) => {
                     this.loadMarkers();
                });
                $('#clear_geomap').click((ev) => {
                     this._clearMarkers(ev);
                });
                $('#clear_last_geomap').click((ev) => {
                     this._clearLastMarker(ev);
                });
                $('#create_geomap_lines').click((ev) => {
                     this._readMarkers(ev);
                });
            }, 1000);
            return this._super();
        },
        addMarker: function() {
            var marker = new google.maps.Marker({
                position: this.location,
                label: this.labels[this.labelIndex++ % this.labels.length],
                map: this.map
            });
            this.markersArray.push(marker);
            this.polylineData.push(this.location);
            if (this.polylineData.length > 1) {
                this._clearPolylines();
                this.createPolyline();
            };
            this._refresh_total();
        },
        loadMarkers: function() {
            this._clearMarkers();
            this._rpc({
                model: 'geometer.location.marker',
                method: 'load_markers',
                args: [this.loc_obj.id],
            }).then( (res) => {
                this.loadedMarkers = res;
                if (this.loadedMarkers) {
                    for (var i = 0; i < this.loadedMarkers.length; i++) {
                        var db_marker = this.loadedMarkers[i];
                        var marker = new google.maps.Marker({
                            position: {lat: db_marker.lat, lng: db_marker.lng},
                            label: db_marker.name || db_marker.sequence,
                            map: this.map
                        });
                        this.labelIndex++;
                        this.markersArray.push(marker);
                        this.polylineData.push({lat: db_marker.lat, lng: db_marker.lng});
                    };
                    if (this.polylineData.length > 1) {
                        this._clearPolylines();
                        this.createPolyline();
                    };
                    this._refresh_total();
                    //this.createBounds();
                };
            });
        },
//        createBounds: function () {
//            this.bounds = new google.maps.LatLngBounds();
//            if (this.markersArray) {
//                for (var i = 0; i < this.markersArray.length; i++) {
//                    console.log(this.markersArray[i]);
//                    this.bounds.extend(this.markersArray[i]);
//                };
//                //this.map.setCenter(this.bounds.getCenter());
//                //this.map.fitBounds(this.bounds);
//                console.log('bounds', this.bounds)
//            };
//        },
        createPolyline: function () {
            if (this.polylineData.length > 1) {
                var markline = new google.maps.Polyline({
                    path: this.polylineData,
                    geodesic: true,
                    strokeColor: '#FF0000',
                    strokeOpacity: 1.0,
                    strokeWeight: 2
                });
                markline.setMap(this.map);
                this.polylines.push(markline);
            };
        },
        _readMarkers: function(ev) {
            var markers_to_save = {};
            this.dist_in_km = 0.0;
            if (this.markersArray.length > 0) {
                for (var i = 0; i < this.markersArray.length; i++) {
                    var marker = this.markersArray[i];
                    var curr_dist = 0;
                    if (i > 0) {
                        curr_dist = this._compute_distance(
                            this.markersArray[i - 1],
                            this.markersArray[i]
                        );
                        this.dist_in_km += curr_dist / 1000;
                    };
                    var marker_obj = {
                        name: marker.label,
                        sequence: i + 1,
                        lat: marker.getPosition().lat(),
                        lng: marker.getPosition().lng(),
                        distance: curr_dist,
                        distance_start: this.dist_in_km,
                        location_id: this.loc_obj.id
                    };
                    markers_to_save[i + 1] = marker_obj
                };
                markers_to_save['own_ctx'] = {
                    uri: this.__parentedParent.$el.context.baseURI,
                    center: this.map.getCenter(),
                    zoom: this.map.getZoom(),
                };
                this._rpc({
                    model: 'geometer.location.marker',
                    method: 'create_markers',
                    args: [markers_to_save],
                }).then( (res) => {
                    this.do_action(res);
                    //this.__parentedParent._updateView
                });
            };
        },
        _compute_distance: function (marker_from, marker_to) {
            var distanceInMeters = google.maps.geometry.spherical.computeDistanceBetween(
                marker_from.getPosition(),
                marker_to.getPosition(),
            );
            return distanceInMeters;
        },
        _compute_total_distance: function () {
            this.dist_in_km = 0;
            if (this.markersArray.length > 1) {
                for (var i = 0; i < this.markersArray.length; i++) {
                    var curr_dist = 0;
                    if (i > 0) {
                        curr_dist = this._compute_distance(
                            this.markersArray[i - 1],
                            this.markersArray[i]
                        );
                        this.dist_in_km += curr_dist / 1000;
                    };
                };
            };
        },
        _refresh_total: function () {
            this._compute_total_distance();
            $('#geomap_total_dist').html(
                (Math.round(this.dist_in_km * 100) / 100).toString() + " km"
            );
        },
        _clearMarkers: function(ev) {
            for (var i = 0; i < this.markersArray.length; i++) {
                this.markersArray[i].setMap(null);
                this.markersArray[i] = null;
            };
            this._clearPolylines();
            this.markersArray = [];
            this.polylineData = [];
            this.labelIndex = 0;
            this._refresh_total();
        },
        _clearLastMarker: function () {
            if (this.markersArray.length > 0) {
                var last_marker = this.markersArray.pop();
                last_marker.setMap(null);
                last_marker = null;
                this.polylineData.pop();
                this.labelIndex--;
            };
            if (this.polylines.length > 0) {
                var last_line = this.polylines.pop();
                last_line.setMap(null);
                last_line = null;
            };
            this.createPolyline();
            this._refresh_total();
        },
        _clearPolylines: function () {
            this.polylines.forEach((line, nr) => {
                if (line) {
                    line.setMap(null);
                    line = null;
                };
            });
            this.polylines = [];
        },
    });
    widgetRegistry.add('GEOMAPSHOW', geoManager);
});



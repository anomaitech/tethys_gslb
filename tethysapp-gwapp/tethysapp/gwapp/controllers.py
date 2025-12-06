from tethys_sdk.routing import controller
from tethys_sdk.layouts import MapLayout
from tethys_sdk.gizmos import Button, TextInput, SelectInput
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib import messages
import json
import csv
import io
import os
from pathlib import Path
import pandas as pd
from datetime import datetime
from .app import App


@controller(name="home", app_workspace=True)
class GWAppMapLayout(MapLayout):
    app = App
    base_template = f'{App.package}/base.html'
    map_title = 'Groundwater Wells Map'
    map_subtitle = 'Interactive Well Data Visualization'
    
    def compose_layers(self, request, map_view, app_workspace, *args, **kwargs):
        """
        Add well layers to the MapLayout.
        """
        # Load wells data from uploaded files or use sample data
        wells_geojson = self.load_wells_data(app_workspace)
        if not wells_geojson:
            # Sample wells data if no uploaded data
            wells_geojson = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [-111.9, 40.7]  # Sample coordinates (longitude, latitude)
                        },
                        "properties": {
                            "well_id": "WELL_001",
                            "name": "Sample Well 1",
                            "depth": 150
                        }
                    },
                    {
                        "type": "Feature", 
                        "geometry": {
                            "type": "Point",
                            "coordinates": [-111.8, 40.8]
                        },
                        "properties": {
                            "well_id": "WELL_002", 
                            "name": "Sample Well 2",
                            "depth": 200
                        }
                    }
                ]
            }
        
        wells_layer = self.build_geojson_layer(
            geojson=wells_geojson,
            layer_name='wells',
            layer_title='Groundwater Wells',
            layer_variable='wells',
            visible=True,
            selectable=True,
            plottable=True,
        )
        
        layer_groups = [
            self.build_layer_group(
                id='groundwater-data',
                display_name='Groundwater Data',
                layer_control='checkbox',
                layers=[wells_layer]
            )
        ]
        
        return layer_groups

    def load_wells_data(self, app_workspace):
        """
        Load wells data from uploaded files.
        """
        try:
            wells_file = Path(app_workspace.path) / 'wells.json'
            if wells_file.exists():
                with open(wells_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading wells data: {e}")
        return None

    @classmethod
    def get_vector_style_map(cls):
        return {
            'Point': {'ol.style.Style': {
                'image': {'ol.style.Circle': {
                    'radius': 8,
                    'fill': {'ol.style.Fill': {
                        'color': 'blue',
                    }},
                    'stroke': {'ol.style.Stroke': {
                        'color': 'white',
                        'width': 2
                    }}
                }}
            }}
        }


@controller
def upload_wells(request):
    """
    Controller for uploading well data CSV.
    """
    context = {
        'page_title': 'Upload Well Data'
    }
    return App.render(request, 'upload_wells.html', context)


@controller
def upload_measurements(request):
    """
    Controller for uploading well measurements CSV.
    """
    context = {
        'page_title': 'Upload Measurements'
    }
    return App.render(request, 'upload_measurements.html', context)

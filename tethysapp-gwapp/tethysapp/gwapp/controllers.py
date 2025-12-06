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
from .sqlite_db import get_db_manager


@controller(name="basins", app_workspace=True)
def basins_list(request, app_workspace):
    """
    Display a list of all imported basins with their data.
    """
    try:
        db = get_db_manager(workspace_path=app_workspace.path)
        basins = db.get_all_basins()
        
        # Get scheme information for each basin
        for basin in basins:
            scheme = db.get_scheme_by_id(basin['scheme_id'])
            basin['scheme_name'] = scheme['name'] if scheme else 'Unknown'
        
        context = {
            'basins': basins,
            'app': App
        }
        
        return render(request, 'gwapp/basins_list.html', context)
    except Exception as e:
        import traceback
        print(f"Error loading basins list: {e}")
        print(traceback.format_exc())
        return render(request, 'gwapp/basins_list.html', {
            'basins': [],
            'error': str(e),
            'app': App
        })


@controller(name="home", app_workspace=True)
def home(request, app_workspace):
    """
    Custom home controller with basins list and map
    """
    try:
        # Get all basins with their schema information
        db = get_db_manager(workspace_path=app_workspace.path)
        basins = db.get_all_basins()
        
        print(f"🔍 Home controller: Found {len(basins)} basins")
        
        # Get scheme information for each basin
        for basin in basins:
            scheme = db.get_scheme_by_id(basin['scheme_id'])
            basin['scheme_name'] = scheme['name'] if scheme else 'Unknown'
            print(f"  - Basin: {basin.get('name', 'Unknown')}, Schema: {basin.get('scheme_name', 'Unknown')}")
        
        # Initial empty wells data (will be loaded when schema is clicked)
        wells_geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        
        basins_json = json.dumps(basins)
        print(f"🔍 Basins JSON length: {len(basins_json)}")
        print(f"🔍 Basins JSON (first 200 chars): {basins_json[:200]}")
        
        context = {
            'basins': basins_json,  # Pass as JSON for JavaScript
            'wells_geojson': json.dumps(wells_geojson),
            'app': App,
            'map_title': 'Groundwater Wells Map',
            'map_subtitle': 'Interactive Well Data Visualization'
        }
    except Exception as e:
        import traceback
        print(f"Error loading home: {e}")
        print(traceback.format_exc())
        context = {
            'basins': '[]',  # Pass as JSON string for JavaScript
            'wells_geojson': json.dumps({"type": "FeatureCollection", "features": []}),
            'app': App,
            'map_title': 'Groundwater Wells Map',
            'map_subtitle': 'Interactive Well Data Visualization'
        }
    
    try:
        # Try to render the custom map template
        return render(request, 'gwapp/custom_map.html', context)
    except Exception as e:
        import traceback
        print("=" * 80)
        print("ERROR RENDERING CUSTOM_MAP TEMPLATE")
        print("=" * 80)
        print(f"Error: {e}")
        print(traceback.format_exc())
        print("=" * 80)
        # Fallback to simple home template
        try:
            return render(request, 'gwapp/home.html', context)
        except Exception as e2:
            print(f"ERROR RENDERING HOME TEMPLATE: {e2}")
            # Last resort - return a simple response
            from django.http import HttpResponse
            try:
                from django.urls import reverse
                upload_url = reverse('gwapp:upload_data')
            except:
                upload_url = '/apps/gwapp/upload-data/'
            return HttpResponse(f"""
                <html><body>
                    <h1>GWapp - Groundwater Well Analysis</h1>
                    <p>Error loading map view. Please check server logs.</p>
                    <a href="{upload_url}">Upload Data</a>
                </body></html>
            """)


def load_wells_data(app_workspace, max_features=1000):
    """
    Load wells data from uploaded files.
    Limits the number of features for performance.
    """
    try:
        wells_file = Path(app_workspace.path) / 'wells.json'
        if wells_file.exists():
            with open(wells_file, 'r') as f:
                data = json.load(f)
                
                # Limit features for performance
                if data and 'features' in data and len(data['features']) > max_features:
                    print(f"⚠️ Limiting wells data from {len(data['features'])} to {max_features} features for performance")
                    data['features'] = data['features'][:max_features]
                
                return data
    except Exception as e:
        print(f"Error loading wells data: {e}")
    return None


@controller(name="map_legacy", app_workspace=True)
class GWAppMapLayout(MapLayout):
    app = App
    base_template = 'gwapp/base.html'
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
        
        # Get basin name from request or use default
        basin_name = request.GET.get('basin', 'Salt Lake Basin')
        
        layer_groups = [
            self.build_layer_group(
                id='basin-wells',
                display_name=basin_name,
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


@controller(app_workspace=True)
def upload_data(request, app_workspace):
    """
    Controller for uploading combined well and measurement data CSV.
    """
    if request.method == 'POST':
        if 'data_file' in request.FILES:
            return handle_csv_upload(request, app_workspace)
    
    context = {
        'page_title': 'Upload Well Data CSV'
    }
    return App.render(request, 'upload_data.html', context)


@controller(app_workspace=True)
def column_mapping(request, app_workspace):
    """
    Controller for mapping CSV columns to database fields using selected schema.
    """
    try:
        if request.method == 'POST':
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'confirm_mapping' in request.POST:
                return process_column_mapping(request, app_workspace)
    except Exception as e:
        import traceback
        print("=" * 80)
        print("ERROR IN column_mapping CONTROLLER")
        print("=" * 80)
        print(traceback.format_exc())
        print("=" * 80)
        return JsonResponse({
            'success': False,
            'error': f'Controller error: {str(e)}'
        }, status=500)
    
    # Get uploaded file info from session
    file_type = request.GET.get('type', 'combined')
    temp_file = request.session.get('data_temp_file')
    
    if not temp_file:
        messages.error(request, 'No file found for column mapping.')
        return App.render(request, 'upload_data.html', {})
    
    # Read CSV headers and sample data
    try:
        df = pd.read_csv(temp_file, nrows=10)
        columns = df.columns.tolist()
    except Exception as e:
        messages.error(request, f'Error reading file: {str(e)}')
        return App.render(request, 'upload_data.html', {})
    
    # Load all available schemes
    db = get_db_manager(workspace_path=app_workspace.path)
    schemes = db.get_all_schemes()
    
    # Get selected scheme ID from request or use first scheme
    selected_scheme_id = request.GET.get('scheme_id')
    selected_scheme = None
    
    if selected_scheme_id:
        try:
            selected_scheme = db.get_scheme_by_id(int(selected_scheme_id))
        except (ValueError, TypeError):
            pass
    
    if not selected_scheme and schemes:
        selected_scheme = schemes[0]
    
    # Extract fields from selected scheme
    required_fields = []
    optional_fields = []
    
    if selected_scheme:
        required_fields = [col['name'] for col in selected_scheme.get('required_columns', [])]
        optional_fields = [col['name'] for col in selected_scheme.get('optional_columns', [])]
    else:
        # Fallback to default fields if no schemes exist
        required_fields = ['well_id', 'latitude', 'longitude', 'date', 'water_table_elevation']
        optional_fields = ['well_name', 'well_depth', 'elevation', 'measurement_time', 'notes', 'quality_flag']
    
    # Auto-suggest mappings based on column names
    # Convert to list of tuples for easier template access
    suggested_mappings = {}
    suggested_mappings_list = []
    if selected_scheme:
        for csv_col in columns:
            csv_col_lower = csv_col.lower().strip()
            
            # Check against schema column names
            all_schema_cols = required_fields + optional_fields
            for schema_col in all_schema_cols:
                if csv_col_lower == schema_col.lower() or csv_col_lower in schema_col.lower() or schema_col.lower() in csv_col_lower:
                    suggested_mappings[schema_col] = csv_col
                    suggested_mappings_list.append((schema_col, csv_col))
                    break
    
    # Serialize schemes to JSON for JavaScript
    import json as json_lib
    schemes_json = json_lib.dumps(schemes) if schemes else '[]'
    selected_scheme_json = json_lib.dumps(selected_scheme) if selected_scheme else None
    columns_json = json_lib.dumps(columns) if columns else '[]'
    sample_data_json = json_lib.dumps(df.head(5).to_dict('records') if len(df) > 0 else [])
    
    context = {
        'page_title': 'Map CSV Columns to Database Fields',
        'file_type': file_type,
        'columns': columns,
        'columns_json': columns_json,
        'schemes': schemes,
        'schemes_json': schemes_json,
        'selected_scheme': selected_scheme,
        'selected_scheme_json': selected_scheme_json,
        'required_fields': required_fields,
        'optional_fields': optional_fields,
        'sample_data': df.head(5).to_dict('records') if len(df) > 0 else [],
        'sample_data_json': sample_data_json,
        'suggested_mappings': suggested_mappings,
        'suggested_mappings_list': suggested_mappings_list,
        'auto_detected_count': len(suggested_mappings)
    }
    
    return App.render(request, 'column_mapping.html', context)


def handle_csv_upload(request, app_workspace):
    """
    Handle combined well and measurement data CSV upload.
    """
    file = request.FILES['data_file']
    
    # Save temporary file
    temp_dir = Path(app_workspace.path) / 'temp'
    temp_dir.mkdir(exist_ok=True)
    temp_file_path = temp_dir / f'welldata_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    with open(temp_file_path, 'wb') as f:
        for chunk in file.chunks():
            f.write(chunk)
    
    # Store file path in session for column mapping
    request.session['data_temp_file'] = str(temp_file_path)
    
    # Get default scheme if available
    db = get_db_manager(workspace_path=app_workspace.path)
    schemes = db.get_all_schemes()
    scheme_param = ''
    if schemes:
        scheme_param = f'&scheme_id={schemes[0]["id"]}'
    
    # Check if coming from settings page
    if request.POST.get('from_settings') or request.headers.get('Referer', '').endswith('/settings/'):
        request.session['return_to_settings'] = True
    
    # Redirect to column mapping
    return JsonResponse({
        'success': True,
        'redirect_url': f'/apps/gwapp/column-mapping/?type=combined{scheme_param}'
    })


def process_column_mapping(request, app_workspace):
    """
    Process the column mapping and save data using the selected schema.
    """
    try:
        temp_file = request.session.get('data_temp_file')
        
        if not temp_file:
            return JsonResponse({'success': False, 'error': 'File not found.'}, status=400)
        
        if not os.path.exists(temp_file):
            return JsonResponse({'success': False, 'error': f'Temp file not found: {temp_file}'}, status=400)
        # Get selected scheme
        scheme_id = request.POST.get('scheme_id')
        if not scheme_id:
            return JsonResponse({'success': False, 'error': 'No schema selected.'}, status=400)
        
        # Get database manager and load scheme
        db = get_db_manager(workspace_path=app_workspace.path)
        scheme = db.get_scheme_by_id(int(scheme_id))
        
        if not scheme:
            return JsonResponse({'success': False, 'error': 'Schema not found.'}, status=404)
        
        # Read the CSV with mapped columns
        df = pd.read_csv(temp_file)
        
        # Get all column mappings from the form
        column_mappings = {}
        all_scheme_columns = scheme['required_columns'] + scheme['optional_columns']
        
        for col_def in all_scheme_columns:
            col_name = col_def['name']
            csv_col = request.POST.get(f'{col_name}_mapping')
            if csv_col:
                column_mappings[col_name] = csv_col
        
        # Validate required columns are mapped
        required_col_names = [col['name'] for col in scheme['required_columns']]
        missing_required = [col for col in required_col_names if col not in column_mappings]
        if missing_required:
            return JsonResponse({
                'success': False, 
                'error': f'Missing required column mappings: {", ".join(missing_required)}'
            }, status=400)
        
        # Process CSV rows and create data rows
        data_rows = []
        skipped_rows = 0
        
        for idx, row in df.iterrows():
            try:
                data_row = {}
                
                # Map each schema column to CSV column value
                for col_def in all_scheme_columns:
                    col_name = col_def['name']
                    data_type = col_def.get('data_type', 'TEXT')
                    
                    if col_name in column_mappings:
                        csv_col = column_mappings[col_name]
                        raw_value = row[csv_col]
                        
                        # Convert value based on data type
                        if pd.isna(raw_value):
                            if col_def in scheme['required_columns']:
                                # Required field is missing - skip row or use default
                                default_val = col_def.get('default_value')
                                if default_val:
                                    data_row[col_name] = default_val
                                else:
                                    raise ValueError(f'Required field {col_name} is missing')
                            else:
                                # Optional field - use default or None
                                default_val = col_def.get('default_value')
                                data_row[col_name] = default_val if default_val else None
                        else:
                            # Convert based on data type
                            if data_type == 'INTEGER':
                                data_row[col_name] = int(float(raw_value))
                            elif data_type == 'REAL':
                                data_row[col_name] = float(raw_value)
                            elif data_type in ['DATE', 'DATETIME']:
                                try:
                                    date_obj = pd.to_datetime(raw_value)
                                    if data_type == 'DATE':
                                        data_row[col_name] = date_obj.strftime('%Y-%m-%d')
                                    else:
                                        data_row[col_name] = date_obj.strftime('%Y-%m-%d %H:%M:%S')
                                except:
                                    data_row[col_name] = str(raw_value)
                            elif data_type == 'BOOLEAN':
                                data_row[col_name] = bool(raw_value)
                            else:  # TEXT
                                data_row[col_name] = str(raw_value)
                    else:
                        # Column not mapped - use default if available
                        default_val = col_def.get('default_value')
                        if default_val:
                            data_row[col_name] = default_val
                        elif col_def in scheme['required_columns']:
                            raise ValueError(f'Required field {col_name} not mapped')
                
                data_rows.append(data_row)
                
            except (ValueError, KeyError, TypeError) as e:
                skipped_rows += 1
                print(f"Skipping row {idx}: {e}")
                continue
        
        if not data_rows:
            return JsonResponse({
                'success': False, 
                'error': 'No valid rows found in CSV file. Please check your data and column mappings.'
            }, status=400)
        
        # Get basin configuration
        basin_name = request.POST.get('basin_name', '').strip()
        basin_description = request.POST.get('basin_description', '').strip()
        plot_latitude = request.POST.get('plot_latitude', '').strip()
        plot_longitude = request.POST.get('plot_longitude', '').strip()
        plot_date = request.POST.get('plot_date', '').strip()
        plot_values = request.POST.getlist('plot_value')  # Get multiple values
        
        # Validate basin configuration
        if not basin_name:
            return JsonResponse({'success': False, 'error': 'Basin name is required'}, status=400)
        
        if not plot_latitude or not plot_longitude or not plot_date or not plot_values:
            return JsonResponse({
                'success': False, 
                'error': 'All plotting columns (latitude, longitude, date, and value) are required'
            }, status=400)
        
        # Verify plotting columns exist in the CSV file
        csv_columns = set(df.columns.tolist())
        if plot_latitude not in csv_columns:
            return JsonResponse({
                'success': False, 
                'error': f'Latitude column "{plot_latitude}" not found in CSV file'
            }, status=400)
        if plot_longitude not in csv_columns:
            return JsonResponse({
                'success': False, 
                'error': f'Longitude column "{plot_longitude}" not found in CSV file'
            }, status=400)
        if plot_date not in csv_columns:
            return JsonResponse({
                'success': False, 
                'error': f'Date column "{plot_date}" not found in CSV file'
            }, status=400)
        for val_col in plot_values:
            if val_col not in csv_columns:
                return JsonResponse({
                    'success': False, 
                    'error': f'Value column "{val_col}" not found in CSV file'
                }, status=400)
        
        # Generate basin table name
        import re
        table_name_base = re.sub(r'[^a-zA-Z0-9_]', '_', basin_name.lower())
        table_name_base = re.sub(r'_+', '_', table_name_base).strip('_')
        if not table_name_base or not table_name_base[0].isalpha():
            table_name_base = f"basin_{table_name_base}"
        basin_table_name = f"basin_{table_name_base}"
        
        # Check if basin already exists
        existing_basin = db.get_basin_by_name(basin_name)
        
        if existing_basin:
            # Use existing basin, but drop and recreate table to ensure correct structure
            basin_id = existing_basin['id']
            basin_table_name = existing_basin['table_name']
            print(f"Using existing basin: {basin_name} (ID: {basin_id}, Table: {basin_table_name})")
            
            # Drop existing table and recreate with correct structure (auto-incrementing id)
            try:
                with db.get_connection() as conn:
                    cursor = conn.cursor()
                    print(f"⚠️  Dropping existing table {basin_table_name} to recreate with correct structure...")
                    cursor.execute(f"DROP TABLE IF EXISTS \"{basin_table_name}\"")
                    conn.commit()
                    # Recreate table with correct structure (auto-incrementing id, not well_id as PK)
                    db.create_basin_table(basin_table_name, all_scheme_columns, column_mappings)
                    print(f"✅ Recreated table {basin_table_name} with auto-incrementing id as primary key")
            except Exception as e:
                print(f"⚠️  Error recreating table: {e}")
                import traceback
                traceback.print_exc()
                # Continue anyway - will try to insert data
        else:
            # Create new basin table with mapped columns
            db.create_basin_table(basin_table_name, all_scheme_columns, column_mappings)
            
            # Create basin record
            value_columns_str = ','.join(plot_values)
            basin_id = db.create_basin(
                name=basin_name,
                description=basin_description,
                latitude_column=plot_latitude,
                longitude_column=plot_longitude,
                date_column=plot_date,
                value_columns=value_columns_str,
                scheme_id=int(scheme_id),
                table_name=basin_table_name
            )
            print(f"Created new basin: {basin_name} (ID: {basin_id})")
        
        # Insert data into the basin table
        db.insert_data_into_basin_table(basin_table_name, data_rows)
        
        # Also insert data into the scheme's table (for backward compatibility)
        db.insert_data_into_scheme_table(int(scheme_id), data_rows)
        
        # Also create GeoJSON for map visualization (if lat/lon columns exist)
        wells_geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        
        # Try to find latitude and longitude columns
        lat_col_name = None
        lon_col_name = None
        id_col_name = None
        
        for col_def in all_scheme_columns:
            col_name = col_def['name'].lower()
            if 'lat' in col_name:
                lat_col_name = col_def['name']
            if 'lon' in col_name or 'lng' in col_name:
                lon_col_name = col_def['name']
            if 'id' in col_name or col_def.get('is_primary_key'):
                id_col_name = col_def['name']
        
        if lat_col_name and lon_col_name and id_col_name:
            for row in data_rows:
                try:
                    lat = float(row.get(lat_col_name, 0))
                    lon = float(row.get(lon_col_name, 0))
                    feature_id = str(row.get(id_col_name, f"feature_{len(wells_geojson['features'])}"))
                    
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [lon, lat]
                        },
                        "properties": row
                    }
                    wells_geojson['features'].append(feature)
                except (ValueError, KeyError):
                    continue
        
        # Save GeoJSON for map
        if wells_geojson['features']:
            data_dir = Path(app_workspace.path)
            wells_geojson_file = data_dir / 'wells.json'
            with open(wells_geojson_file, 'w') as f:
                json.dump(wells_geojson, f)
        
        # Clean up temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
        request.session.pop('data_temp_file', None)
        
        success_msg = f'Successfully imported {len(data_rows)} records into basin "{basin_name}"'
        if skipped_rows > 0:
            success_msg += f' ({skipped_rows} rows skipped)'
        
        # Check if user wants to return to settings
        redirect_url = '/apps/gwapp/'
        if request.session.get('return_to_settings') or request.POST.get('return_to_settings'):
            redirect_url = '/apps/gwapp/settings/?tab=basins'
            request.session.pop('return_to_settings', None)
        
        return JsonResponse({
            'success': True,
            'message': success_msg,
            'redirect_url': redirect_url,
            'basin_id': basin_id,
            'basin_name': basin_name
        })
        
    except Exception as e:
        import traceback
        import sys
        error_msg = str(e)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        # Log detailed error information
        print("=" * 80)
        print("ERROR PROCESSING COLUMN MAPPING")
        print("=" * 80)
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {error_msg}")
        print(f"Traceback:")
        print(traceback.format_exc())
        print("=" * 80)
        
        # Return JSON error response
        try:
            return JsonResponse({
                'success': False,
                'error': f'Error processing file: {error_msg}',
                'error_type': type(e).__name__
            }, status=500)
        except Exception as json_error:
            # If even JsonResponse fails, log it
            print(f"CRITICAL: Could not return JsonResponse: {json_error}")
            # Return a simple text response
            from django.http import HttpResponse
            return HttpResponse(
                json.dumps({
                    'success': False,
                    'error': f'Error processing file: {error_msg}'
                }),
                content_type='application/json',
                status=500
            )


@controller(app_workspace=True)
def get_well_timeseries(request, app_workspace):
    """
    API endpoint to get time series data for a specific well.
    """
    well_id = request.GET.get('well_id')
    
    if not well_id:
        return JsonResponse({'error': 'Well ID required'}, status=400)
    
    try:
        # Load timeseries data
        timeseries_file = Path(app_workspace.path) / 'timeseries.json'
        if not timeseries_file.exists():
            return JsonResponse({'data': []})
        
        with open(timeseries_file, 'r') as f:
            timeseries_data = json.load(f)
        
        well_data = timeseries_data.get(well_id, [])
        
        return JsonResponse({
            'well_id': well_id,
            'data': well_data
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@controller(app_workspace=True)
def settings(request, app_workspace):
    """
    Settings page with tabs for Schema Management, Upload File, and Imported Basins
    """
    try:
        # Get all basins for the Imported Basins tab
        db = get_db_manager(workspace_path=app_workspace.path)
        basins = db.get_all_basins()
        
        # Get scheme information for each basin
        for basin in basins:
            scheme = db.get_scheme_by_id(basin['scheme_id'])
            basin['scheme_name'] = scheme['name'] if scheme else 'Unknown'
        
        # Get active tab from URL parameter
        active_tab = request.GET.get('tab', 'schema')
        
        context = {
            'app': App,
            'page_title': 'Settings & Management',
            'page_subtitle': 'Manage Schemas, Upload Files, and View Imported Data',
            'basins': basins,
            'active_tab': active_tab
        }
    except Exception as e:
        import traceback
        print(f"Error loading settings: {e}")
        print(traceback.format_exc())
        context = {
            'app': App,
            'page_title': 'Settings & Management',
            'page_subtitle': 'Manage Schemas, Upload Files, and View Imported Data',
            'basins': [],
            'active_tab': 'schema'
        }
    
    return render(request, 'gwapp/settings.html', context)


@controller(name="get_basin_points", app_workspace=True)
def get_basin_points(request, app_workspace):
    """
    Get unique lat/lon points for a basin
    """
    try:
        basin_id = request.GET.get('basin_id')
        if not basin_id:
            return JsonResponse({'success': False, 'error': 'Basin ID required'}, status=400)
        
        db = get_db_manager(workspace_path=app_workspace.path)
        points = db.get_unique_points_for_basin(int(basin_id))
        
        print(f"🔍 get_basin_points: Retrieved {len(points)} points for basin {basin_id}")
        
        # Convert to GeoJSON format
        geojson = {
            "type": "FeatureCollection",
            "features": []
        }
        
        for point in points:
            properties = {
                "latitude": point['latitude'],
                "longitude": point['longitude']
            }
            # Include well_id if available
            if 'well_id' in point:
                properties['well_id'] = point['well_id']
            if 'measurement_count' in point:
                properties['measurement_count'] = point['measurement_count']
            
            geojson['features'].append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": point['coordinates']
                },
                "properties": properties
            })
        
        print(f"🔍 get_basin_points: Returning {len(geojson['features'])} features")
        return JsonResponse({'success': True, 'points': geojson})
        
    except Exception as e:
        import traceback
        print(f"Error getting basin points: {e}")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@controller(name="get_point_timeseries", app_workspace=True)
def get_point_timeseries(request, app_workspace):
    """
    Get time series data for a specific lat/lon point or well_id
    """
    try:
        basin_id = request.GET.get('basin_id')
        latitude = request.GET.get('latitude')
        longitude = request.GET.get('longitude')
        well_id = request.GET.get('well_id')
        
        if not basin_id:
            return JsonResponse({'success': False, 'error': 'Basin ID required'}, status=400)
        
        # Prefer well_id if provided, otherwise use lat/lon
        if well_id:
            if not latitude or not longitude:
                return JsonResponse({'success': False, 'error': 'Latitude and longitude required when using well_id'}, status=400)
        elif not latitude or not longitude:
            return JsonResponse({'success': False, 'error': 'Either well_id or latitude/longitude required'}, status=400)
        
        db = get_db_manager(workspace_path=app_workspace.path)
        
        if well_id:
            timeseries = db.get_timeseries_for_well(
                int(basin_id),
                well_id
            )
        else:
            timeseries = db.get_timeseries_for_point(
                int(basin_id),
                float(latitude),
                float(longitude)
            )
        
        return JsonResponse({'success': True, 'timeseries': timeseries})
        
    except Exception as e:
        import traceback
        print(f"Error getting point timeseries: {e}")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================================================
# API ENDPOINTS
# ============================================================================

@controller(name="api_basins", app_workspace=True)
def api_basins(request, app_workspace):
    """API: List all basins"""
    try:
        if not app_workspace:
            return JsonResponse({'success': False, 'error': 'App workspace not available'}, status=500)
        
        db = get_db_manager(workspace_path=app_workspace.path)
        basins = db.get_all_basins()
        
        # Get scheme information for each basin
        for basin in basins:
            scheme = db.get_scheme_by_id(basin['scheme_id'])
            basin['scheme_name'] = scheme['name'] if scheme else 'Unknown'
            # Parse value columns
            if isinstance(basin.get('value_columns'), str):
                basin['value_columns'] = [col.strip() for col in basin['value_columns'].split(',')]
        
        return JsonResponse({
            'success': True,
            'count': len(basins),
            'basins': basins
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in api_basins: {e}")
        print(error_trace)
        return JsonResponse({
            'success': False, 
            'error': str(e),
            'error_type': type(e).__name__
        }, status=500)


@controller(name="api_basin_detail", app_workspace=True)
def api_basin_detail(request, basin_id, app_workspace):
    """API: Get basin details"""
    try:
        db = get_db_manager(workspace_path=app_workspace.path)
        basin = db.get_basin_by_id(int(basin_id))
        
        if not basin:
            return JsonResponse({'success': False, 'error': 'Basin not found'}, status=404)
        
        # Get scheme information
        scheme = db.get_scheme_by_id(basin['scheme_id'])
        basin['scheme_name'] = scheme['name'] if scheme else 'Unknown'
        basin['scheme'] = scheme
        
        # Parse value columns
        if isinstance(basin.get('value_columns'), str):
            basin['value_columns'] = [col.strip() for col in basin['value_columns'].split(',')]
        
        return JsonResponse({
            'success': True,
            'basin': basin
        })
    except Exception as e:
        import traceback
        print(f"Error in api_basin_detail: {e}")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@controller(name="api_basin_wells", app_workspace=True)
def api_basin_wells(request, basin_id, app_workspace):
    """API: Get all wells in a basin"""
    try:
        min_measurements = int(request.GET.get('min_measurements', 1))
        
        db = get_db_manager(workspace_path=app_workspace.path)
        basin = db.get_basin_by_id(int(basin_id))
        
        if not basin:
            return JsonResponse({'success': False, 'error': 'Basin not found'}, status=404)
        
        table_name = basin['table_name']
        
        # Find well_id column
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info(\"{table_name}\")")
            columns = cursor.fetchall()
            actual_columns = [col[1] for col in columns]
            
            well_id_col = None
            for col in actual_columns:
                if 'well' in col.lower() and 'id' in col.lower():
                    well_id_col = col
                    break
            
            if not well_id_col:
                return JsonResponse({'success': False, 'error': 'Well ID column not found'}, status=404)
            
            # Find lat/lon columns
            lat_col = None
            lon_col = None
            csv_lat_col = basin['latitude_column']
            csv_lon_col = basin['longitude_column']
            
            scheme = db.get_scheme_by_id(basin['scheme_id'])
            all_scheme_columns = scheme.get('required_columns', []) + scheme.get('optional_columns', [])
            
            if csv_lat_col in actual_columns:
                lat_col = csv_lat_col
            else:
                for schema_col in all_scheme_columns:
                    schema_col_name = schema_col.get('name', '')
                    if schema_col_name in actual_columns and 'lat' in schema_col_name.lower():
                        lat_col = schema_col_name
                        break
            
            if csv_lon_col in actual_columns:
                lon_col = csv_lon_col
            else:
                for schema_col in all_scheme_columns:
                    schema_col_name = schema_col.get('name', '')
                    if schema_col_name in actual_columns and ('lon' in schema_col_name.lower() or 'lng' in schema_col_name.lower()):
                        lon_col = schema_col_name
                        break
            
            # Get wells with measurement counts
            query = f'''
                SELECT 
                    "{well_id_col}" as well_id,
                    AVG("{lat_col}") as avg_lat,
                    AVG("{lon_col}") as avg_lon,
                    COUNT(*) as measurement_count
                FROM "{table_name}"
                WHERE "{well_id_col}" IS NOT NULL
            '''
            
            if lat_col and lon_col:
                query += f' AND "{lat_col}" IS NOT NULL AND "{lon_col}" IS NOT NULL'
            
            query += f' GROUP BY "{well_id_col}" HAVING COUNT(*) >= {min_measurements} ORDER BY measurement_count DESC'
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            wells = []
            for row in rows:
                wells.append({
                    'well_id': row[0],
                    'latitude': float(row[1]) if row[1] else None,
                    'longitude': float(row[2]) if row[2] else None,
                    'measurement_count': int(row[3])
                })
        
        return JsonResponse({
            'success': True,
            'count': len(wells),
            'min_measurements': min_measurements,
            'wells': wells
        })
    except Exception as e:
        import traceback
        print(f"Error in api_basin_wells: {e}")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@controller(name="api_well_timeseries", app_workspace=True)
def api_well_timeseries(request, basin_id, well_id, app_workspace):
    """API: Get time series for a specific well"""
    try:
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        db = get_db_manager(workspace_path=app_workspace.path)
        timeseries = db.get_timeseries_for_well(int(basin_id), well_id)
        
        if not timeseries:
            return JsonResponse({
                'success': True,
                'count': 0,
                'timeseries': []
            })
        
        # Filter by date range if provided
        if start_date or end_date:
            filtered = []
            for record in timeseries:
                record_date = record.get('date', '')
                if start_date and record_date < start_date:
                    continue
                if end_date and record_date > end_date:
                    continue
                filtered.append(record)
            timeseries = filtered
        
        return JsonResponse({
            'success': True,
            'count': len(timeseries),
            'well_id': well_id,
            'start_date': start_date,
            'end_date': end_date,
            'timeseries': timeseries
        })
    except Exception as e:
        import traceback
        print(f"Error in api_well_timeseries: {e}")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@controller(name="api_basin_statistics", app_workspace=True)
def api_basin_statistics(request, basin_id, app_workspace):
    """API: Get basin statistics"""
    try:
        db = get_db_manager(workspace_path=app_workspace.path)
        basin = db.get_basin_by_id(int(basin_id))
        
        if not basin:
            return JsonResponse({'success': False, 'error': 'Basin not found'}, status=404)
        
        table_name = basin['table_name']
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Find columns
            cursor.execute(f"PRAGMA table_info(\"{table_name}\")")
            columns = cursor.fetchall()
            actual_columns = [col[1] for col in columns]
            
            well_id_col = None
            date_col = None
            value_cols = []
            
            for col in actual_columns:
                if 'well' in col.lower() and 'id' in col.lower():
                    well_id_col = col
                if 'date' in col.lower() or col.lower() == 'date':
                    date_col = col
            
            # Get value columns from basin config
            value_cols_str = basin.get('value_columns', '')
            if isinstance(value_cols_str, str):
                csv_value_cols = [col.strip() for col in value_cols_str.split(',')]
            else:
                csv_value_cols = value_cols_str if isinstance(value_cols_str, list) else []
            
            for csv_val_col in csv_value_cols:
                if csv_val_col in actual_columns:
                    value_cols.append(csv_val_col)
            
            # Calculate statistics
            stats = {
                'total_records': 0,
                'unique_wells': 0,
                'date_range': {},
                'measurement_distribution': {},
                'value_statistics': {}
            }
            
            # Total records
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            stats['total_records'] = cursor.fetchone()[0]
            
            # Unique wells
            if well_id_col:
                cursor.execute(f'SELECT COUNT(DISTINCT "{well_id_col}") FROM "{table_name}"')
                stats['unique_wells'] = cursor.fetchone()[0]
            
            # Date range
            if date_col:
                cursor.execute(f'SELECT MIN("{date_col}"), MAX("{date_col}") FROM "{table_name}" WHERE "{date_col}" IS NOT NULL')
                date_range = cursor.fetchone()
                if date_range and date_range[0]:
                    stats['date_range'] = {
                        'min': date_range[0],
                        'max': date_range[1]
                    }
            
            # Measurement distribution
            if well_id_col:
                cursor.execute(f'''
                    SELECT measurement_count, COUNT(*) as well_count
                    FROM (
                        SELECT "{well_id_col}", COUNT(*) as measurement_count
                        FROM "{table_name}"
                        GROUP BY "{well_id_col}"
                    )
                    GROUP BY measurement_count
                    ORDER BY measurement_count DESC
                    LIMIT 20
                ''')
                dist = cursor.fetchall()
                stats['measurement_distribution'] = {
                    str(row[0]): row[1] for row in dist
                }
            
            # Value statistics
            for val_col in value_cols:
                cursor.execute(f'''
                    SELECT 
                        COUNT(*) as count,
                        MIN("{val_col}") as min_val,
                        MAX("{val_col}") as max_val,
                        AVG("{val_col}") as avg_val
                    FROM "{table_name}"
                    WHERE "{val_col}" IS NOT NULL
                ''')
                val_stats = cursor.fetchone()
                if val_stats:
                    stats['value_statistics'][val_col] = {
                        'count': val_stats[0],
                        'min': float(val_stats[1]) if val_stats[1] else None,
                        'max': float(val_stats[2]) if val_stats[2] else None,
                        'avg': float(val_stats[3]) if val_stats[3] else None
                    }
        
        return JsonResponse({
            'success': True,
            'basin_id': int(basin_id),
            'basin_name': basin['name'],
            'statistics': stats
        })
    except Exception as e:
        import traceback
        print(f"Error in api_basin_statistics: {e}")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@controller(name="api_basin_query", app_workspace=True)
def api_basin_query(request, basin_id, app_workspace):
    """API: Query basin data with filters"""
    try:
        if request.method != 'POST':
            return JsonResponse({'success': False, 'error': 'POST method required'}, status=405)
        
        import json
        body = json.loads(request.body)
        
        well_ids = body.get('well_ids', [])
        start_date = body.get('start_date')
        end_date = body.get('end_date')
        limit = body.get('limit', 1000)
        offset = body.get('offset', 0)
        
        db = get_db_manager(workspace_path=app_workspace.path)
        basin = db.get_basin_by_id(int(basin_id))
        
        if not basin:
            return JsonResponse({'success': False, 'error': 'Basin not found'}, status=404)
        
        table_name = basin['table_name']
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Find columns
            cursor.execute(f"PRAGMA table_info(\"{table_name}\")")
            columns = cursor.fetchall()
            actual_columns = [col[1] for col in columns]
            
            well_id_col = None
            date_col = None
            
            for col in actual_columns:
                if 'well' in col.lower() and 'id' in col.lower():
                    well_id_col = col
                if 'date' in col.lower() or col.lower() == 'date':
                    date_col = col
            
            # Build query
            query = f'SELECT * FROM "{table_name}" WHERE 1=1'
            params = []
            
            if well_ids and well_id_col:
                placeholders = ','.join(['?' for _ in well_ids])
                query += f' AND "{well_id_col}" IN ({placeholders})'
                params.extend(well_ids)
            
            if start_date and date_col:
                query += f' AND "{date_col}" >= ?'
                params.append(start_date)
            
            if end_date and date_col:
                query += f' AND "{date_col}" <= ?'
                params.append(end_date)
            
            query += f' LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to list of dicts
            column_names = [col[1] for col in columns]
            results = []
            for row in rows:
                record = {}
                for i, col_name in enumerate(column_names):
                    record[col_name] = row[i]
                results.append(record)
        
        return JsonResponse({
            'success': True,
            'count': len(results),
            'limit': limit,
            'offset': offset,
            'data': results
        })
    except Exception as e:
        import traceback
        print(f"Error in api_basin_query: {e}")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@controller(name="api_schemes", app_workspace=True)
def api_schemes(request, app_workspace):
    """API: List all schemes"""
    try:
        if not app_workspace:
            return JsonResponse({'success': False, 'error': 'App workspace not available'}, status=500)
        
        db = get_db_manager(workspace_path=app_workspace.path)
        schemes = db.get_all_schemes()
        
        return JsonResponse({
            'success': True,
            'count': len(schemes),
            'schemes': schemes
        })
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in api_schemes: {e}")
        print(error_trace)
        return JsonResponse({
            'success': False, 
            'error': str(e),
            'error_type': type(e).__name__
        }, status=500)


@controller(name="save_column_mapping", app_workspace=True)
def save_column_mapping(request, app_workspace):
    """
    Save column mapping configuration (supports both old format and new schemes format)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        # Get database manager with app workspace path
        db = get_db_manager(workspace_path=app_workspace.path)
        
        # Handle JSON content type
        if request.content_type == 'application/json':
            import json as json_lib
            data = json_lib.loads(request.body)
        else:
            # Handle form data (legacy support)
            mapping_json = request.POST.get('mapping')
            if not mapping_json:
                return JsonResponse({'error': 'Mapping data required'}, status=400)
            data = json.loads(mapping_json)
        
        # Check for operation-based requests first (create/update/delete)
        operation = data.get('operation')
        
        if operation in ['create', 'update', 'delete']:
            # Handle single scheme operations
            if operation == 'create':
                # Create new scheme
                scheme_data = data.get('scheme')
                if not scheme_data:
                    return JsonResponse({'success': False, 'error': 'Scheme data required for create operation'}, status=400)
                
                # Validate scheme name
                scheme_name = scheme_data.get('name', '').strip()
                if not scheme_name:
                    return JsonResponse({'success': False, 'error': 'Scheme name is required'}, status=400)
                
                # Ensure first required column is primary key if none specified
                required_cols = scheme_data.get('required_columns', [])
                if not required_cols:
                    return JsonResponse({'success': False, 'error': 'At least one required column is needed'}, status=400)
                
                # Ensure all required columns have data_type
                for col in required_cols:
                    if not col.get('name'):
                        return JsonResponse({'success': False, 'error': 'All columns must have a name'}, status=400)
                    if not col.get('data_type'):
                        col['data_type'] = 'TEXT'  # Default to TEXT if not specified
                
                if not any(col.get('is_primary_key') for col in required_cols):
                    required_cols[0]['is_primary_key'] = True
                
                # Ensure optional columns have data_type
                optional_cols = scheme_data.get('optional_columns', [])
                for col in optional_cols:
                    if not col.get('name'):
                        return JsonResponse({'success': False, 'error': 'All columns must have a name'}, status=400)
                    if not col.get('data_type'):
                        col['data_type'] = 'TEXT'  # Default to TEXT if not specified
                
                try:
                    result = db.create_scheme(
                        name=scheme_name,
                        description=scheme_data.get('description', '').strip(),
                        required_columns=required_cols,
                        optional_columns=optional_cols
                    )
                    
                    # Ensure result has all required fields
                    if result:
                        print(f"✅ Created scheme: ID={result.get('id')}, Name={result.get('name')}")
                        print(f"   Required columns: {len(result.get('required_columns', []))}")
                        print(f"   Optional columns: {len(result.get('optional_columns', []))}")
                    else:
                        print("⚠️ Warning: create_scheme returned None")
                    
                    return JsonResponse({'success': True, 'scheme': result, 'message': 'Scheme created successfully'})
                except ValueError as e:
                    return JsonResponse({'success': False, 'error': str(e)}, status=400)
                except Exception as e:
                    import traceback
                    print(f"Error creating scheme: {e}")
                    print(traceback.format_exc())
                    return JsonResponse({'success': False, 'error': f'Error creating scheme: {str(e)}'}, status=500)
            
            elif operation == 'update':
                # Update existing scheme
                scheme_id = data.get('scheme_id')
                scheme_data = data.get('scheme')
                
                if not scheme_id or not scheme_data:
                    return JsonResponse({'success': False, 'error': 'Scheme ID and data required for update operation'}, status=400)
                
                # Validate scheme name
                scheme_name = scheme_data.get('name', '').strip()
                if not scheme_name:
                    return JsonResponse({'success': False, 'error': 'Scheme name is required'}, status=400)
                
                # Ensure first required column is primary key if none specified
                required_cols = scheme_data.get('required_columns', [])
                if not required_cols:
                    return JsonResponse({'success': False, 'error': 'At least one required column is needed'}, status=400)
                
                # Ensure all columns have data_type
                for col in required_cols:
                    if not col.get('name'):
                        return JsonResponse({'success': False, 'error': 'All columns must have a name'}, status=400)
                    if not col.get('data_type'):
                        col['data_type'] = 'TEXT'
                
                optional_cols = scheme_data.get('optional_columns', [])
                for col in optional_cols:
                    if not col.get('name'):
                        return JsonResponse({'success': False, 'error': 'All columns must have a name'}, status=400)
                    if not col.get('data_type'):
                        col['data_type'] = 'TEXT'
                
                if not any(col.get('is_primary_key') for col in required_cols):
                    required_cols[0]['is_primary_key'] = True
                
                try:
                    result = db.update_scheme(
                        scheme_id=scheme_id,
                        name=scheme_name,
                        description=scheme_data.get('description', '').strip(),
                        required_columns=required_cols,
                        optional_columns=optional_cols
                    )
                    
                    return JsonResponse({'success': True, 'scheme': result, 'message': 'Scheme updated successfully'})
                except ValueError as e:
                    return JsonResponse({'success': False, 'error': str(e)}, status=400)
                except Exception as e:
                    import traceback
                    print(f"Error updating scheme: {e}")
                    print(traceback.format_exc())
                    return JsonResponse({'success': False, 'error': f'Error updating scheme: {str(e)}'}, status=500)
            
            elif operation == 'delete':
                # Delete scheme
                scheme_id = data.get('scheme_id')
                if not scheme_id:
                    return JsonResponse({'success': False, 'error': 'Scheme ID required for delete operation'}, status=400)
                
                db.delete_scheme(scheme_id)
                return JsonResponse({'success': True, 'message': 'Scheme deleted successfully'})
        
        # Check if this is the bulk schemes format (multiple schemes)
        elif 'schemes' in data:
            # Handle bulk schemes operations - save all schemes (replace all) - fallback to file
            mapping_file = os.path.join(app_workspace.path, 'column_mapping.json')
            with open(mapping_file, 'w') as f:
                json.dump(data, f, indent=2)
            return JsonResponse({'success': True, 'message': 'Column mapping saved successfully'})
        
        else:
            # Legacy format - save to file
            mapping_file = os.path.join(app_workspace.path, 'column_mapping.json')
            with open(mapping_file, 'w') as f:
                json.dump(data, f, indent=2)
            return JsonResponse({'success': True, 'message': 'Column mapping saved successfully'})
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Error saving column mapping: {error_msg}")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': error_msg}, status=500)


@controller(name="get_column_mapping", app_workspace=True)
def get_column_mapping(request, app_workspace):
    """
    Get saved column mapping configuration (supports both old format and new schemes format)
    """
    try:
        # Get database manager with app workspace path
        db = get_db_manager(workspace_path=app_workspace.path)
        
        schemes = db.get_all_schemes()
        
        print(f"📋 get_column_mapping: Found {len(schemes) if schemes else 0} schemes")
        if schemes:
            for i, scheme in enumerate(schemes):
                print(f"   [{i}] ID: {scheme.get('id')}, Name: {scheme.get('name')}, Required: {len(scheme.get('required_columns', []))}, Optional: {len(scheme.get('optional_columns', []))}")
        
        if schemes:
            return JsonResponse({'success': True, 'schemes': schemes})
        else:
            # Fallback to file-based storage if no schemes in database
            mapping_file = os.path.join(app_workspace.path, 'column_mapping.json')
            
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r') as f:
                    data = json.load(f)
                
                # Check if it's the new schemes format
                if 'schemes' in data:
                    return JsonResponse({'success': True, 'schemes': data['schemes']})
                else:
                    # Legacy format - convert to schemes format
                    return JsonResponse({'success': True, 'mapping': data})
            else:
                # Return empty list - database should have been initialized with default scheme
                return JsonResponse({'success': True, 'schemes': []})
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Error loading column mapping: {error_msg}")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': error_msg}, status=500)


@controller(name="delete_basin", app_workspace=True)
def delete_basin(request, app_workspace):
    """
    Delete a basin and its associated data table
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Only POST method allowed'}, status=405)
    
    try:
        basin_id = request.POST.get('basin_id') or request.GET.get('basin_id')
        
        if not basin_id:
            return JsonResponse({'success': False, 'error': 'basin_id is required'}, status=400)
        
        try:
            basin_id = int(basin_id)
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid basin_id'}, status=400)
        
        # Get database manager
        db = get_db_manager(workspace_path=app_workspace.path)
        
        # Get basin info before deletion for response
        basin = db.get_basin_by_id(basin_id)
        if not basin:
            return JsonResponse({'success': False, 'error': f'Basin with ID {basin_id} not found'}, status=404)
        
        # Delete the basin
        db.delete_basin(basin_id)
        
        return JsonResponse({
            'success': True,
            'message': f'Basin "{basin["name"]}" deleted successfully',
            'basin_id': basin_id
        })
        
    except ValueError as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Error deleting basin: {error_msg}")
        print(traceback.format_exc())
        return JsonResponse({'success': False, 'error': error_msg}, status=500)

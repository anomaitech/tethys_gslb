from tethys_sdk.routing import controller
from tethys_sdk.gizmos import Button, MapView, MVDraw, MVView, TextInput, SelectInput
from .app import App


@controller
def home(request):
    """
    Controller for the app home page - Groundwater Dashboard
    """
    # Navigation buttons for groundwater features
    wells_button = Button(
        display_text='Well Management',
        name='wells-button',
        icon='bi bi-geo-alt',
        style='primary',
        href=App.reverse('wells'),
        attributes={
            'data-bs-toggle': 'tooltip',
            'data-bs-placement': 'top',
            'title': 'Manage groundwater wells'
        }
    )

    aquifer_button = Button(
        display_text='Aquifer Analysis',
        name='aquifer-button',
        icon='bi bi-layers',
        style='info',
        href=App.reverse('aquifer_analysis'),
        attributes={
            'data-bs-toggle': 'tooltip',
            'data-bs-placement': 'top',
            'title': 'Analyze aquifer properties'
        }
    )

    quality_button = Button(
        display_text='Water Quality',
        name='quality-button',
        icon='bi bi-droplet',
        style='success',
        href=App.reverse('water_quality'),
        attributes={
            'data-bs-toggle': 'tooltip',
            'data-bs-placement': 'top',
            'title': 'Monitor water quality'
        }
    )

    modeling_button = Button(
        display_text='Groundwater Modeling',
        name='modeling-button',
        icon='bi bi-graph-up',
        style='warning',
        href=App.reverse('modeling'),
        attributes={
            'data-bs-toggle': 'tooltip',
            'data-bs-placement': 'top',
            'title': 'Run groundwater models'
        }
    )

    # Simple map view for groundwater overview
    map_view = MapView(
        height='400px',
        width='100%',
        basemap={'Esri': ['World_Imagery']},
        center=[-111.64, 40.25],  # Utah coordinates
        zoom=10,
        max_zoom=18,
        min_zoom=2
    )

    context = {
        'wells_button': wells_button,
        'aquifer_button': aquifer_button,
        'quality_button': quality_button,
        'modeling_button': modeling_button,
        'map_view': map_view,
        'page_title': 'Groundwater APP Dashboard'
    }

    return App.render(request, 'home.html', context)


@controller
def wells(request):
    """
    Controller for well management page
    """
    # Well location input form
    well_name_input = TextInput(
        display_text='Well Name',
        name='well_name',
        placeholder='Enter well name...'
    )

    well_depth_input = TextInput(
        display_text='Well Depth (m)',
        name='well_depth',
        placeholder='Enter well depth in meters...'
    )

    well_type_select = SelectInput(
        display_text='Well Type',
        name='well_type',
        options=[
            ('monitoring', 'Monitoring Well'),
            ('production', 'Production Well'),
            ('injection', 'Injection Well'),
            ('observation', 'Observation Well')
        ]
    )

    # Map for well locations
    wells_map = MapView(
        height='500px',
        width='100%',
        basemap={'OpenStreetMap': ['OpenStreetMap']},
        center=[-111.64, 40.25],
        zoom=12,
        max_zoom=18,
        min_zoom=2
    )

    add_well_button = Button(
        display_text='Add Well',
        name='add-well',
        icon='bi bi-plus-circle',
        style='success'
    )

    context = {
        'well_name_input': well_name_input,
        'well_depth_input': well_depth_input,
        'well_type_select': well_type_select,
        'wells_map': wells_map,
        'add_well_button': add_well_button,
        'page_title': 'Well Management'
    }

    return App.render(request, 'wells.html', context)


@controller
def aquifer_analysis(request):
    """
    Controller for aquifer analysis page
    """
    context = {
        'page_title': 'Aquifer Analysis'
    }
    return App.render(request, 'aquifer_analysis.html', context)


@controller
def water_quality(request):
    """
    Controller for water quality monitoring page
    """
    context = {
        'page_title': 'Water Quality Monitoring'
    }
    return App.render(request, 'water_quality.html', context)


@controller
def modeling(request):
    """
    Controller for groundwater modeling page
    """
    context = {
        'page_title': 'Groundwater Modeling'
    }
    return App.render(request, 'modeling.html', context)

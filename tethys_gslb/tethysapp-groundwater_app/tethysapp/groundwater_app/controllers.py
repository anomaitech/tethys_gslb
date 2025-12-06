from tethys_sdk.routing import controller
from tethys_sdk.gizmos import Button
from .app import App


@controller
def home(request):
    """
    Controller for the app home page.
    """
    context = {}
    return App.render(request, 'home.html', context)


@controller
def wells(request):
    """
    Controller for wells management page.
    """
    context = {}
    return App.render(request, 'wells.html', context)


@controller
def aquifer_analysis(request):
    """
    Controller for aquifer analysis page.
    """
    context = {}
    return App.render(request, 'aquifer_analysis.html', context)


@controller
def water_quality(request):
    """
    Controller for water quality monitoring page.
    """
    context = {}
    return App.render(request, 'water_quality.html', context)


@controller
def modeling(request):
    """
    Controller for groundwater modeling page.
    """
    context = {}
    return App.render(request, 'modeling.html', context)

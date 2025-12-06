from tethys_sdk.routing import controller
from tethys_sdk.gizmos import Button
from .app import App


@controller
def home(request):
    """
    Controller for the app home page.
    """
    save_button = Button(
        display_text='',
        name='save-button',
        icon='save',
        style='success',
        attributes={
            'data-bs-toggle': 'tooltip',
            'data-bs-placement': 'top',
            'title': 'Save'
        }
    )

    edit_button = Button(
        display_text='',
        name='edit-button',
        icon='pen',
        style='warning',
        attributes={
            'data-bs-toggle': 'tooltip',
            'data-bs-placement': 'top',
            'title': 'Edit'
        }
    )

    remove_button = Button(
        display_text='',
        name='remove-button',
        icon='trash',
        style='danger',
        attributes={
            'data-bs-toggle': 'tooltip',
            'data-bs-placement': 'top',
            'title': 'Remove'
        }
    )

    previous_button = Button(
        display_text='Previous',
        name='previous-button',
        attributes={
            'data-bs-toggle': 'tooltip',
            'data-bs-placement': 'top',
            'title': 'Previous'
        }
    )

    next_button = Button(
        display_text='Next',
        name='next-button',
        attributes={
            'data-bs-toggle': 'tooltip',
            'data-bs-placement': 'top',
            'title': 'Next'
        }
    )

    context = {
        'save_button': save_button,
        'edit_button': edit_button,
        'remove_button': remove_button,
        'previous_button': previous_button,
        'next_button': next_button
    }

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

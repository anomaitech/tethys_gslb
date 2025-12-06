from tethys_sdk.base import TethysAppBase


class App(TethysAppBase):
    """
    Tethys app class for GWapp.
    """
    name = 'GWapp'
    description = ''
    package = 'gwapp'  # WARNING: Do not change this value
    index = 'home'
    icon = f'{package}/images/icon.gif'
    root_url = 'gwapp'
    color = '#192a56'
    tags = ''
    enable_feedback = False
    feedback_emails = []

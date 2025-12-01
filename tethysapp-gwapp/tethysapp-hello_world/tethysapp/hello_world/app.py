from tethys_sdk.base import TethysAppBase


class App(TethysAppBase):
    """
    Tethys app class for Hello World.
    """
    name = 'Hello World'
    description = ''
    package = 'hello_world'  # WARNING: Do not change this value
    index = 'home'
    icon = f'{package}/images/icon.gif'
    root_url = 'hello-world'
    color = '#2c3e50'
    tags = ''
    enable_feedback = False
    feedback_emails = []

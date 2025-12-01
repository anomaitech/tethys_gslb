from tethys_sdk.base import TethysAppBase
from tethys_sdk.app_settings import PersistentStoreDatabaseSetting


class App(TethysAppBase):
    """
    Tethys app class for Groundwater APP.
    """
    name = 'Groundwater APP'
    description = 'Its intended to serve as a platform for groundwater related projects'
    package = 'gwapp'  # WARNING: Do not change this value
    index = 'home'
    icon = f'{package}/images/icon.gif'
    root_url = 'gwapp'
    color = '#27ae60'  # Changed to green for groundwater theme
    tags = 'Groundwater experts,Groundwater,Remote sensing'
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers for different groundwater functionalities
        """
        from tethys_sdk.routing import url_map_maker
        
        UrlMap = url_map_maker(self.root_url)
        
        url_maps = (
            UrlMap(
                name='home',
                url='gwapp',
                controller='gwapp.controllers.home'
            ),
            UrlMap(
                name='wells',
                url='gwapp/wells',
                controller='gwapp.controllers.wells'
            ),
            UrlMap(
                name='aquifer_analysis',
                url='gwapp/aquifer-analysis',
                controller='gwapp.controllers.aquifer_analysis'
            ),
            UrlMap(
                name='water_quality',
                url='gwapp/water-quality',
                controller='gwapp.controllers.water_quality'
            ),
            UrlMap(
                name='modeling',
                url='gwapp/modeling',
                controller='gwapp.controllers.modeling'
            ),
        )
        
        return url_maps

    def persistent_store_settings(self):
        """
        Define Persistent Store Settings for groundwater data
        """
        ps_settings = (
            PersistentStoreDatabaseSetting(
                name='groundwater_db',
                description='Database for groundwater data storage',
                initializer='gwapp.init_stores.init_groundwater_db',
                required=True
            ),
        )
        return ps_settings

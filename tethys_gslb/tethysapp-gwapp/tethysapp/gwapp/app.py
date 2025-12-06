from tethys_sdk.base import TethysAppBase
from tethys_sdk.app_settings import CustomSetting


class App(TethysAppBase):
    """
    Tethys app class for Groundwater APP.
    """
    name = 'Groundwater APP'
    description = 'A comprehensive groundwater management and analysis application'
    package = 'gwapp'  # WARNING: Do not change this value
    index = 'home'
    icon = f'{package}/images/icon.gif'
    root_url = 'gwapp'
    color = '#2980b9'
    tags = 'Groundwater,Hydrology,Water Management'
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers
        """
        from tethys_sdk.routing import url_map_maker
        from tethysapp.gwapp.controllers import home, wells, aquifer_analysis, water_quality, modeling

        UrlMap = url_map_maker(self.root_url)

        url_maps = (
            UrlMap(
                name='home',
                url='gwapp',
                controller='tethysapp.gwapp.controllers.home',
            ),
            UrlMap(
                name='wells',
                url='gwapp/wells',
                controller='tethysapp.gwapp.controllers.wells',
            ),
            UrlMap(
                name='aquifer_analysis',
                url='gwapp/aquifer-analysis',
                controller='tethysapp.gwapp.controllers.aquifer_analysis',
            ),
            UrlMap(
                name='water_quality',
                url='gwapp/water-quality',
                controller='tethysapp.gwapp.controllers.water_quality',
            ),
            UrlMap(
                name='modeling',
                url='gwapp/modeling',
                controller='tethysapp.gwapp.controllers.modeling',
            ),
        )

        return url_maps

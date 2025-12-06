from tethys_sdk.base import TethysAppBase
from tethys_sdk.app_settings import CustomSetting


class App(TethysAppBase):
    """
    Tethys app class for Groundwater APP.
    """
    name = 'Groundwater APP'
    description = 'A comprehensive groundwater management and analysis application'
    package = 'groundwater_app'  # WARNING: Do not change this value
    index = 'home'
    icon = f'{package}/images/icon.gif'
    root_url = 'groundwater-app'
    color = '#2980b9'
    tags = 'Groundwater,Hydrology,Water Management'
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers
        """
        from tethys_sdk.routing import url_map_maker
        from tethysapp.groundwater_app.controllers import home, wells, aquifer_analysis, water_quality, modeling

        UrlMap = url_map_maker(self.root_url)

        url_maps = (
            UrlMap(
                name='home',
                url='apps/groundwater-app',
                controller='tethysapp.groundwater_app.controllers.home',
            ),
            UrlMap(
                name='wells',
                url='groundwater-app/wells',
                controller='tethysapp.groundwater_app.controllers.wells',
            ),
            UrlMap(
                name='aquifer_analysis',
                url='groundwater-app/aquifer-analysis',
                controller='tethysapp.groundwater_app.controllers.aquifer_analysis',
            ),
            UrlMap(
                name='water_quality',
                url='groundwater-app/water-quality',
                controller='tethysapp.groundwater_app.controllers.water_quality',
            ),
            UrlMap(
                name='modeling',
                url='groundwater-app/modeling',
                controller='tethysapp.groundwater_app.controllers.modeling',
            ),
        )

        return url_maps

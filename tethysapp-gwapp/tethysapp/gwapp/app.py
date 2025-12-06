from tethys_sdk.base import TethysAppBase
from tethys_sdk.app_settings import CustomSetting, PersistentStoreDatabaseSetting


class App(TethysAppBase):
    """
    Tethys app class for GWapp.
    """
    name = 'GWapp'
    description = 'Groundwater Well Analysis and Visualization Platform'
    package = 'gwapp'  # WARNING: Do not change this value
    index = 'home'
    icon = f'{package}/images/icon.gif'
    root_url = 'gwapp'
    color = '#192a56'
    tags = 'Groundwater,Wells,Time Series,Water Resources'
    enable_feedback = False
    feedback_emails = []

    def url_maps(self):
        """
        Add controllers
        """
        from tethys_sdk.routing import url_map_maker

        url_map_maker = url_map_maker(self.root_url)
        
        url_maps = [
            url_map_maker(
                name='home',
                url='',
                controller=f'{self.package}.controllers.home'
            ),
            url_map_maker(
                name='upload_data',
                url='upload-data/',
                controller=f'{self.package}.controllers.upload_data'
            ),
            url_map_maker(
                name='column_mapping',
                url='column-mapping/',
                controller=f'{self.package}.controllers.column_mapping'
            ),
            url_map_maker(
                name='get_well_timeseries',
                url='api/well-timeseries/',
                controller=f'{self.package}.controllers.get_well_timeseries'
            ),
            url_map_maker(
                name='settings',
                url='settings/',
                controller=f'{self.package}.controllers.settings'
            ),
            url_map_maker(
                name='save_column_mapping',
                url='save-column-mapping/',
                controller=f'{self.package}.controllers.save_column_mapping'
            ),
            url_map_maker(
                name='get_column_mapping',
                url='get-column-mapping/',
                controller=f'{self.package}.controllers.get_column_mapping'
            ),
            url_map_maker(
                name='basins',
                url='basins/',
                controller=f'{self.package}.controllers.basins_list'
            ),
            url_map_maker(
                name='get_basin_points',
                url='api/get-basin-points/',
                controller=f'{self.package}.controllers.get_basin_points'
            ),
            url_map_maker(
                name='get_point_timeseries',
                url='api/get-point-timeseries/',
                controller=f'{self.package}.controllers.get_point_timeseries'
            ),
            # API Endpoints
            url_map_maker(
                name='api_basins',
                url='api/basins/',
                controller=f'{self.package}.controllers.api_basins'
            ),
            url_map_maker(
                name='api_basin_detail',
                url='api/basins/(?P<basin_id>[0-9]+)/',
                controller=f'{self.package}.controllers.api_basin_detail'
            ),
            url_map_maker(
                name='api_basin_wells',
                url='api/basins/(?P<basin_id>[0-9]+)/wells/',
                controller=f'{self.package}.controllers.api_basin_wells'
            ),
            url_map_maker(
                name='api_well_timeseries',
                url='api/basins/(?P<basin_id>[0-9]+)/wells/(?P<well_id>[^/]+)/timeseries/',
                controller=f'{self.package}.controllers.api_well_timeseries'
            ),
            url_map_maker(
                name='api_basin_statistics',
                url='api/basins/(?P<basin_id>[0-9]+)/statistics/',
                controller=f'{self.package}.controllers.api_basin_statistics'
            ),
            url_map_maker(
                name='api_basin_query',
                url='api/basins/(?P<basin_id>[0-9]+)/query/',
                controller=f'{self.package}.controllers.api_basin_query'
            ),
            url_map_maker(
                name='api_schemes',
                url='api/schemes/',
                controller=f'{self.package}.controllers.api_schemes'
            ),
            url_map_maker(
                name='delete_basin',
                url='api/delete-basin/',
                controller=f'{self.package}.controllers.delete_basin'
            ),
        ]

        return url_maps

    def persistent_store_settings(self):
        """
        Define Persistent Store Settings.
        """
        ps_settings = (
            PersistentStoreDatabaseSetting(
                name='gwapp_db',
                description='Database for GWapp',
                initializer='gwapp.model.init_gwapp_db',
                required=False
            ),
        )

        return ps_settings

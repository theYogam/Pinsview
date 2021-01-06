from django.conf.urls import patterns, include, url
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import admin

from pinsview.views import save_optical_fiber_position, save_pin_position, \
    delete_old_way, save_live_optical_fiber_coords, BaseView, filter_network_data, \
    find_lines, is_registered_member, search, get_agent_installation, get_selected_fiber, get_selected_pin, \
    get_recent_equipments, Network, change_pin_position, grab_fibers, grab_pins, save_pin, grab_pin_info, \
    update_fibers_distance, check_new_fiber, check_new_pin, check_data_integrity, check_line_update, Statistic, \
    get_specific_fiber_data, get_specific_pin_data, get_updated_fibers, load_equipments_by_city, grab_fiber_info, \
    get_asset_event_log, save_event_log, grab_event_log_detail, grab_offline_pins, update_pin_cities,\
    save_asset_config, grab_asset_config, save_prospect, update_prospect_status

from admin_panel import *

SIGN_IN = 'login'
_extra_context = BaseView().get_context_data()

admin.autodiscover()

urlpatterns = patterns(
    '',
    url(r'^$', login_required()(Network.as_view()), name='network'),

    url(r'^changeCategory/$', ChangePinCategory.as_view(), name='change_pincategory'),
    url(r'^changeCategory/(?P<object_id>[-\w]+)$', ChangePinCategory.as_view(), name='change_pincategory'),
    url(r'^categories$', PinCategoryList.as_view(), name='pincategory_list'),

    url(r'^changePin/$', ChangePin.as_view(), name='change_pin'),
    url(r'^changePin/(?P<object_id>[-\w]+)$', ChangePin.as_view(), name='change_pin'),
    url(r'^pins$', PinList.as_view(), name='pin_list'),

    url(r'^changeCity/$', ChangeCity.as_view(), name='change_city'),
    url(r'^changeCity/(?P<object_id>[-\w]+)$', ChangeCity.as_view(), name='change_city'),
    url(r'^cities$', CityList.as_view(), name='city_list'),

    url(r'^changeZone/$', ChangeZone.as_view(), name='change_zone'),
    url(r'^changeZone/(?P<object_id>[-\w]+)$', ChangeZone.as_view(), name='change_zone'),
    url(r'^zones$', ZoneList.as_view(), name='zone_list'),

    url(r'^changeLogEventType/$', ChangeLogEventType.as_view(), name='change_logeventtype'),
    url(r'^changeLogEventType/(?P<object_id>[-\w]+)$', ChangeLogEventType.as_view(), name='change_logeventtype'),
    url(r'^logEventTypes$', LogEventTypeList.as_view(), name='logeventtype_list'),

    url(r'^changeAssetLog/$', ChangeAssetLog.as_view(), name='change_assetlog'),
    url(r'^changeAssetLog/(?P<object_id>[-\w]+)$', ChangeAssetLog.as_view(), name='change_assetlog'),
    url(r'^assetsLog$', AssetLogList.as_view(), name='assetlog_list'),

    url(r'^changeNeighborhood/$', ChangeNeighborhood.as_view(), name='change_neighborhood'),
    url(r'^changeNeighborhood/(?P<object_id>[-\w]+)$', ChangeNeighborhood.as_view(), name='change_neighborhood'),
    url(r'^neighborhoods$', NeighborhoodList.as_view(), name='neighborhood_list'),


    url(r'^findFiberlines', find_lines, name='find_lines'),
    url(r'^statistics$', user_passes_test(is_registered_member)(Statistic.as_view()), name='statistic'),
    url(r'^save_pin$', save_pin, name='save_pin'),
    url(r'^save_pin_position$', save_pin_position, name='save_pin_position'),
    url(r'^save_live_optical_fiber_coords$', save_live_optical_fiber_coords, name='save_live_optical_fiber_coords'),
    url(r'^filter_network_data$', filter_network_data, name='filter_network_data'),
    url(r'^delete_old_way$', delete_old_way, name='delete_old_way'),
    url(r'^save_fiber_way$', save_optical_fiber_position, name='save_fiber_way'),
    url(r'^full_search$', search, name='search'),
    url(r'^get_selected_pin$', get_selected_pin, name='get_selected_pin'),
    url(r'^get_selected_fiber$', get_selected_fiber, name='get_selected_fiber'),
    url(r'^change_pin_position$', change_pin_position, name='change_pin_position'),
    url(r'^get_agent_installation$', get_agent_installation, name='get_agent_installation'),
    url(r'^get_recent_equipments$', get_recent_equipments, name='get_recent_equipments'),
    url(r'^grab_fibers$', grab_fibers, name='grab_fibers'),
    url(r'^grab_pins$', grab_pins, name='grab_pins'),
    url(r'^grab_pin_info$', grab_pin_info, name='grab_pin_info'),
    url(r'^grab_fiber_info$', grab_fiber_info, name='grab_fiber_info'),
    url(r'^update_fibers_distance$', update_fibers_distance, name='update_fibers_distance'),
    url(r'^check_new_fiber$', check_new_fiber, name='check_new_fiber'),
    url(r'^check_new_pin$', check_new_pin, name='check_new_pin'),
    url(r'^check_pin_data_integrity$', check_data_integrity, name='check_data_integrity'),
    url(r'^check_line_update$', check_line_update, name='check_line_update'),
    url(r'^get_specific_fiber_data$', get_specific_fiber_data, name='get_specific_fiber_data'),
    url(r'^get_specific_pin_data$', get_specific_pin_data, name='get_specific_pin_data'),
    url(r'^get_updated_fibers$', get_updated_fibers, name='get_updated_fibers'),
    url(r'^load_equipments_by_city$', load_equipments_by_city, name='load_equipments_by_city'),

    url(r'^get_asset_event_log$', get_asset_event_log, name='get_asset_event_log'),
    url(r'^save_asset_config$', save_asset_config, name='save_asset_config'),
    url(r'^save_event_log$', save_event_log, name='save_event_log'),
    url(r'^grab_event_log_detail$', grab_event_log_detail, name='grab_event_log_detail'),
    url(r'^grab_asset_config$', grab_asset_config, name='grab_asset_config'),
    url(r'^grab_offline_pins$', grab_offline_pins, name='grab_offline_pins'),

    url(r'^update_pin_cities$', update_pin_cities, name='update_pin_cities'),
    url(r'^save_prospect$', save_prospect, name='save_prospect'),
    url(r'^update_prospect$', update_prospect_status, name='update_prospect_status'),
)


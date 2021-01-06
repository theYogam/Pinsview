from ikwen.core.views import HybridListView, ChangeObjectBase

from pinsview.admin import PinAdmin, PinCategoryAdmin, CityAdmin, ZoneAdmin, LogEventTypeAdmin, NeighborhoodAdmin, AssetLogAdmin

from pinsview.models import Pin, PinCategory, City, Zone, LogEventType, Neighborhood, AssetLog


class PinList(HybridListView):
    model = Pin


class ChangePin(ChangeObjectBase):
    model = Pin
    model_admin = PinAdmin

    # def get_object(self, *args, **kwargs):
    #     if

class PinCategoryList(HybridListView):
    model = PinCategory


class ChangePinCategory(ChangeObjectBase):
    model = PinCategory
    model_admin = PinCategoryAdmin


class CityList(HybridListView):
    model = City


class ChangeCity(ChangeObjectBase):
    model = City
    model_admin = CityAdmin


class ZoneList(HybridListView):
    model = Zone


class ChangeZone(ChangeObjectBase):
    model = Zone
    model_admin = ZoneAdmin


class ChangeLogEventType(ChangeObjectBase):
    model = LogEventType
    model_admin = LogEventTypeAdmin


class LogEventTypeList(HybridListView):
    model = LogEventType


class ChangeAssetLog(ChangeObjectBase):
    model = AssetLog
    model_admin = AssetLogAdmin


class AssetLogList(HybridListView):
    model = AssetLog


class ChangeNeighborhood(ChangeObjectBase):
    model = Neighborhood
    model_admin = NeighborhoodAdmin


class NeighborhoodList(HybridListView):
    model = Neighborhood



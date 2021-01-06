# Create your views here.
import json
import logging
import math

import random
import time
from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.utils.module_loading import import_by_path
from django.utils.translation import gettext as _
from django.views.decorators.cache import never_cache, cache_page
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.utils.decorators import method_decorator
from django.shortcuts import render, get_object_or_404
from django.utils.http import urlsafe_base64_decode, urlunquote, urlquote
from django.contrib.admin.models import LogEntry
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
# import requests
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.hashers import check_password
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.generic.base import TemplateView

from ikwen.accesscontrol.models import Member

# from CreolinkLocalizer import settings
from conf import settings
from pinsview.models import Pin, FiberEventData, PinCategory, Fiber, Zone, City, Operator, AgentProfile, \
    LogEventType, AssetLog, Neighborhood, to_dict

logger = logging.getLogger('ikwen')
# from ajaxuploader.backends.local import LocalUploadBackend
# from ajaxuploader.views.base import AjaxFileUploader

_BOT = 'Bot'


def is_registered_member(user):
    return user.is_authenticated()


class BaseView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super(BaseView, self).get_context_data(**kwargs)
        context['categories'] = PinCategory.objects.all()
        return context


class SignIn(TemplateView):
    template_name = 'login.html'

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            next_url = request.REQUEST.get('next')
            if next_url:
                return HttpResponseRedirect(next_url)
            else:
                next_url_view = getattr(settings, 'LOGIN_REDIRECT_URL', None)
                if next_url_view:
                    next_url = reverse(next_url_view)
                else:
                    next_url = reverse('pinsview:network')
            return HttpResponseRedirect(next_url)
        return super(SignIn, self).get(request, *args, **kwargs)

    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def post(self, request, *args, **kwargs):
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            member = form.get_user()
            login(request, member)
            query_string = request.META.get('QUERY_STRING')
            next_url = request.REQUEST.get('next')
            if next_url:
                # Remove next_url from the original query_string
                next_url = next_url.split('?')[0]
                query_string = urlunquote(query_string).replace('next=%s' % next_url, '').strip('?').strip('&')
            else:
                next_url_view = getattr(settings, 'LOGIN_REDIRECT_URL', None)
                if next_url_view:
                    next_url = reverse(next_url_view)
                else:
                    next_url = reverse('pinsview:network')
            return HttpResponseRedirect(next_url + "?" + query_string)
        else:
            context = self.get_context_data(**kwargs)
            context['login_form'] = form
            if form.errors:
                error_message = getattr(settings, 'IKWEN_LOGIN_FAILED_ERROR_MSG',
                                        _("Invalid username/password or account inactive"))
                context['error_message'] = error_message
            return render(request, 'login.html', context)

FIBER_BLOCK_SIZE = 50
DEVICE_BLOCK_SIZE = 50


class Statistic(BaseView):
    template_name = 'pinsview/statistics.html'

    def get_context_data(self, **kwargs):
        context = super(Statistic, self).get_context_data(**kwargs)
        pins_qs = Pin.objects
        fibers_qs = Fiber.objects
        pin_categories = PinCategory.objects.all()
        #  ALL
        distance = 0
        for fiber in fibers_qs.all():
            distance += fiber.distance / 1000
        context['pending_fiber_count'] = fibers_qs.filter(status=Fiber.PENDING).count()
        context['validated_fiber_count'] = fibers_qs.filter(status=Fiber.VALIDATE).count()
        context['total_fiber_count'] = fibers_qs.all().count()
        context['total_pins_count'] = pins_qs.all().count()
        context['pending_total_pins_count'] = pins_qs.filter(status=Pin.PENDING).count()
        context['validated_total_pins_count'] = pins_qs.filter(status=Pin.VALIDATE).count()
        context['total_fiber_len'] = distance
        # DOUALA
        dla_distance = 0
        dla_pins_qs = pins_qs.filter(city__name='Douala')
        dla_fibers = fibers_qs.filter(city__name='Douala')
        for fiber in dla_fibers:
            dla_distance += fiber.distance / 1000
        context['dla_pending_fiber_count'] = dla_fibers.filter(status=Fiber.PENDING).count()
        context['dla_validated_fiber_count'] = dla_fibers.filter(status=Fiber.VALIDATE).count()
        context['dla_total_fiber_count'] = dla_fibers.count()
        context['dla_total_pins_count'] = dla_pins_qs.count()
        context['dla_pending_total_pins_count'] = dla_pins_qs.filter(status=Pin.PENDING).count()
        context['dla_validated_total_pins_count'] = dla_pins_qs.filter(status=Pin.VALIDATE).count()
        context['dla_total_fiber_len'] = dla_distance
        # yde
        yde_distance = 0
        yde_pins_qs = pins_qs.filter(city__name='Yaounde')
        yde_fibers = fibers_qs.filter(city__name='Yaounde')
        for fiber in dla_fibers:
            yde_distance += fiber.distance / 1000
        context['yde_pending_fiber_count'] = yde_fibers.filter(status=Fiber.PENDING).count()
        context['yde_validated_fiber_count'] = yde_fibers.filter(status=Fiber.VALIDATE).count()
        context['yde_total_fiber_count'] = yde_fibers.count()
        context['yde_total_pins_count'] = yde_pins_qs.count()
        context['yde_pending_total_pins_count'] = yde_pins_qs.filter(status=Pin.PENDING).count()
        context['yde_validated_total_pins_count'] = yde_pins_qs.filter(status=Pin.VALIDATE).count()
        context['yde_total_fiber_len'] = yde_distance
        fiber_groups = []
        pin_groups = []
        yde_fiber_stat = []
        yde_pin_stat = []
        fiber_stat = []
        pin_stat = []
        dla_fiber_stat = []
        dla_pin_stat = []

        dla_pins_qs = pins_qs.filter(city__name='Douala')
        dla_fibers = fibers_qs.filter(city__name='Douala')
        yde_pins_qs = pins_qs.filter(city__name='Yaounde')
        yde_fibers = fibers_qs.filter(city__name='Yaounde')

        for category in pin_categories:
            pins_count = dla_pins_qs.filter(category=category).count()
            pin_stats = {'category': category, 'pins_count': pins_count}
            dla_pin_stat.append(pin_stats)

        context['pins'] = pin_groups
        context['fibers'] = fiber_groups

        context['fiber_stats'] = fiber_stat
        context['pin_stats'] = pin_stat

        context['yde_fiber_stats'] = yde_fiber_stat
        context['yde_pin_stats'] = yde_pin_stat

        context['dla_fiber_stats'] = dla_fiber_stat
        context['dla_pin_stats'] = dla_pin_stat

        return context


def update_pin_city():
    pins_qs = Pin.objects.all()
    city = City.objects
    for pin in pins_qs:
        longitude = float(pin.longitude)
        if 9 <= longitude <= 10:
            c = city.get(name='Douala')
        else:
            c = city.get(name='Yaounde')
        pin.city = c
        pin.save()


class Network(BaseView):
    # template_name = 'pinsview/equipments.html'
    template_name = 'pinsview/network.html'

    def get_context_data(self, **kwargs):

        context = super(Network, self).get_context_data(**kwargs)
        member = self.request.user
        try:
            profile = AgentProfile.objects.get(member=member)
        except:
            profile = AgentProfile.objects.create(member=self.request.user)
        user_cities = profile.city.all()
        default_city = City.objects.get(default=True)

        try:
            context['user_city'] = user_cities[0]
            user_city = user_cities[0]
        except:
            context['user_city'] = default_city
            user_city = default_city
        context['user_profile'] = profile
        context['event_types'] = LogEventType.objects.all()
        context['fiber_blocks'] = 0

        # member = self.request.user
        profile = AgentProfile.objects.get(member=member)
        operator = profile.operator
        all_fiber_count = Fiber.objects.all().count()
        all_pin_count = Pin.objects.all().count()

        if all_fiber_count > 0:
            context['last_fiber_id'] = (Fiber.objects.all().order_by('-id')[0]).id

        if all_pin_count > 0:
            context['last_pin_id'] = (Pin.objects.all().order_by('-id')[0]).id
        context['pin_categories'] = PinCategory.objects.all().order_by('name')
        if member.is_superuser:
            zones = Zone.objects.all()
            context['cities'] = City.objects.all().order_by('name')
            context['zones'] = Zone.objects.all().order_by('name')
        else:
            zones = profile.zone.all()
            context['cities'] = profile.city.all().order_by('name')
            context['zones'] = profile.zone.all().order_by('name')
        context['neighborhoods'] = grab_neighborhoods_from_zones(zones)
        context['media_root'] = settings.MEDIA_URL
        context['member'] = self.request.user
        if self.request.user.is_superuser:
            pin_queryset = Pin.objects.all()
        else:
            agent = AgentProfile.objects.get(member=member)
            pin_queryset = Pin.objects.filter(operator=agent.operator, city=user_city)
        context['pins'] = pin_queryset[0:DEVICE_BLOCK_SIZE]
        offline_pins = Pin.objects.filter(status='offline')
        context['offline_pins_count'] = offline_pins.count()
        context['offline_pins'] = offline_pins
        count_pins = pin_queryset.count()
        pin_blocks = int(math.ceil(float(count_pins) / DEVICE_BLOCK_SIZE))
        context['pin_blocks'] = pin_blocks
        try:
            member_group = member.groups.all()[0]
        except:
            pass
        else:
            context['member_group'] = member_group
        if self.request.user.is_superuser:
            context['operators'] = Operator.objects.all()
            context['show_operators'] = True
        else:
            context['operators'] = operator
            context['show_operators'] = False

        context['pin_list'] = Pin.objects.all()
        context['category_list'] = PinCategory.objects.all()
        return context


def change_date_to_string(date_to_stringify):
    changed_date = '%02d/%02d/%d  %02d:%02d:%02d' % (
        date_to_stringify.year, date_to_stringify.month, date_to_stringify.day, date_to_stringify.hour,
        date_to_stringify.minute, date_to_stringify.second)
    return changed_date


def retrieve_dates_from_interval(string_date):
    date_array = string_date.replace(' - ', '-')
    date_array = string_date.split('-')
    dates = []
    for d in date_array:
        d = d.replace('/', '-')
        dates.append(d.strip())
    return dates


@login_required
def get_only_equipments(request, *args, **kwargs):
    member = request.user
    profile = AgentProfile.objects.get(member=member)
    operator = profile.operator
    if member.is_superuser:
        equipments = Pin.objects.filter(is_active=True)
    else:
        equipments = Pin.objects.filter(operator=operator, is_active=True, city=profile.city)
    response = [equipment.to_dict() for equipment in equipments]
    return HttpResponse(json.dumps({'equipments': response}), 'content-type: text/json', **kwargs)


@login_required
def get_only_fibers(request, *args, **kwargs):
    member = request.user
    profile = AgentProfile.objects.get(member=member)
    operator = profile.operator
    if member.is_superuser:
        fiber_lines = Fiber.objects.filter(distance__gt=0)
    else:
        fiber_lines = Fiber.objects.filter(operator=operator, city=profile.city, distance__gt=0)
    lines = []
    for line in fiber_lines:
        fiber_events = FiberEventData.objects.filter(line=line)
        response = [fiber_event.to_dict() for fiber_event in fiber_events]
        lines.append(response)
    return HttpResponse(json.dumps({'lines': lines}), 'content-type: text/json', **kwargs)


@login_required
def get_equipments_and_fibers(request, *args, **kwargs):
    member = request.user
    profile = AgentProfile.objects.get(member=member)
    operator = profile.operator
    if member.is_superuser:
        fiber_lines = Fiber.objects.all()
    else:
        fiber_lines = Fiber.objects.filter(operator=operator, city=profile.city)
    lines = []
    for line in fiber_lines:
        fiber_events = FiberEventData.objects.filter(line=line)
        response = [fiber_event.to_dict() for fiber_event in fiber_events]
        lines.append(response)

    if member.is_superuser:
        pins = Pin.objects.filter(is_active=True)
    else:
        pins = Pin.objects.filter(is_active=True, operator=operator, city=profile.city)
    equipments = [pin.to_dict() for pin in pins]
    return HttpResponse(json.dumps({'equipments': equipments, 'lines': lines}), 'content-type: text/json', **kwargs)


@login_required
def delete_old_way(request, *args, **kwargs):
    line_id = request.GET.get('line')
    try:
        fiberline = Fiber.objects.get(pk=line_id)
        fiber_event_data = FiberEventData.objects.filter(fiber=fiberline)
        for fiber in fiber_event_data:
            fiber.delete()
    except Fiber.DoesNotExist:
        pass
    return HttpResponse(
        json.dumps({'success': True}),
        content_type='application/json'
    )


@permission_required("pinsview.add_pin")
def save_pin(request, *args, **kwargs):
    description = request.GET.get('description')
    name = request.GET.get('name')
    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')
    category_id = request.GET.get('category')
    formatted_address = request.GET.get('formatted_address')
    agent = AgentProfile.objects.get(member=request.user)
    description = description.replace('\n', ' ')
    category = PinCategory.objects.get(pk=category_id)
    try:
        city = City.objects.get(default=True)
    except:
        city = City.objects.first()
    pin_count = Pin.objects.filter(category=category).count()
    pin = Pin(category=category, longitude=longitude, latitude=latitude, description=description,
              agent=agent, formatted_address=formatted_address, city=city)
    pin.save()
    if not name:
        name = category.name + "_" + str(pin.id) + "_" + str(pin_count)
    pin.name = name
    pin.save()
    try:
        pin.photo = request.FILES['photo']
    except:
        pass
    pin.save()
    return HttpResponse(
        json.dumps({'pin': pin.to_dict()}),
        content_type='application/json'
    )


@permission_required("pinsview.change_pin")
def save_pin_position(request, *args, **kwargs):
    name = request.POST.get('name', '')
    description = request.POST.get('description')
    latitude = request.POST.get('latitude')
    longitude = request.POST.get('longitude')
    category_id = request.POST.get('category')
    user_profile = AgentProfile.objects.get(member=request.user)
    agent = user_profile
    operator = user_profile.operator
    description = description.replace('\n', ' ')
    category = PinCategory.objects.get(pk=category_id)
    pin_position = Pin(category=category, name=name, longitude=longitude, latitude=latitude,
                             description=description, agent=agent, operator=operator, status=Pin.VALIDATE)
    pin_position.save()
    if not name:
        pin_count = Pin.objects.all().count()
        name = category.name + "_" + str(pin_count)
        pin_position.name = name
        pin_position.save()
    try:
        pin_position.photo = request.FILES['photo']
    except:
        pass
    pin_position.save()
    return HttpResponseRedirect(reverse('home') + "?pinPlotted=yes")


@permission_required('pinsview.add_fiber')
def save_optical_fiber_position(request, *args, **kwargs):
    line_id = request.GET.get('line')
    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')
    try:
        fiberline = Fiber.objects.get(pk=line_id)
    except Fiber.DoesNotExist:
        return HttpResponse(
            json.dumps({'error': "An error occured"}),
            content_type='application/json'
        )

    fiberline.save()
    fiber_event_data = FiberEventData(fiber=fiberline, latitude=latitude, longitude=longitude)
    fiber_event_data.save()
    return HttpResponse(
        json.dumps({'success': True}),
        content_type='application/json'
    )


def construct_line_coords(str_coords):
    coords_list = str_coords.split(';')
    coords_list.pop()
    coordinates = []
    for coord in coords_list:
        coord_dimensions = coord.split(',')
        final_coord = {'latitude': coord_dimensions[0], 'longitude': coord_dimensions[1]}
        coordinates.append(final_coord)
    return coordinates


@login_required
@permission_required("pinsview.add_fibereventdata")
def save_live_optical_fiber_coords(request, *args, **kwargs):
    line_id = request.GET.get('line')
    str_coords = request.GET.get('strCoords')
    line_length = request.GET.get('distance')
    coordinates = construct_line_coords(str_coords)
    try:
        fiber_line = Fiber.objects.get(pk=line_id)
    except Fiber.DoesNotExist:
        return HttpResponse(
            json.dumps({'error': "An error occured"}),
            content_type='application/json'
        )
    FiberEventData.objects.filter(fiber=fiber_line).delete()
    drawer = request.user
    drawer_profile = AgentProfile.objects.get(member=drawer)
    fiber_line.agent = drawer_profile
    fiber_line.line_length = line_length
    fiber_line.distance = line_length
    fiber_line.status = Fiber.VALIDATE
    # fiber_id = fiber_line.__dict__
    fiber_line.save()
    for coordinate in coordinates:
        fiber_event_data = FiberEventData(fiber=fiber_line, latitude=coordinate['latitude'],
                                          longitude=coordinate['longitude'])
        fiber_event_data.save()

    lines = []
    fiber_events = FiberEventData.objects.filter(fiber=fiber_line)
    line_coords = []
    for event in fiber_events:
        color = event.fiber.operator.fiber_color
        fiber_line.color = color
        if event.longitude != "0.0" and event.latitude != "0.0":
            line_point = {
                'latitude': event.latitude,
                'longitude': event.longitude,
            }
            line_coords.append(line_point)
    line = {'fiberline': fiber_line.to_dict(), 'line_coords': line_coords}
    lines.append(line)
    return HttpResponse(
        json.dumps({'success': True, 'line': line}),
        content_type='application/json'
    )


def construct_filter_params_list(params_string):
    param_list = params_string.split(',')
    param_list.pop()
    return param_list


@login_required
def filter_network_data(request, *args, **kwargs):
    agent_id = request.GET.get('agentId')
    operators = request.GET.get('operator')
    operator_ids_params = ''

    fiber_status_params = construct_filter_params_list(request.GET.get('fiberStatus'))
    pin_category_ids_params = construct_filter_params_list(request.GET.get('pinCategory'))
    pin_status_params = construct_filter_params_list(request.GET.get('pinStatus'))
    if operators:
        operator_ids_params = construct_filter_params_list(request.GET.get('operator'))

    if agent_id:
        member = User.objects.get(id=agent_id)
        agent = AgentProfile.objects.get(member=member)
        equipments = Pin.objects.filter(agent=agent).order_by('-id')
        fiber_lines = Fiber.objects.filter(agent=agent).order_by('-id')
    else:
        member = request.user
        agent = AgentProfile.objects.get(member=member)
        operator = agent.operator
        if request.user.is_superuser:
            equipments = Pin.objects.all().order_by('-id')
            fiber_lines = Fiber.objects.all().order_by('-id')
        else:
            equipments = Pin.objects.filter(operator=operator).order_by('-id')
            fiber_lines = Fiber.objects.filter(operator=operator).order_by('-id')

    if len(operator_ids_params) > 0:
        operator_list = []
        for operator_id in operator_ids_params:
            operator = Operator.objects.get(id=operator_id)
            operator_list.append(operator)
        equipments = equipments.filter(operator__in=operator_list)
        fiber_lines = Fiber.objects.filter(operator__in=operator_list).order_by('-id')

    if len(pin_category_ids_params) > 0:
        category_list = []
        for category_id in pin_category_ids_params:
            category = PinCategory.objects.get(id=category_id)
            category_list.append(category)
        equipments = equipments.filter(category__in=category_list)
    # else:
    #     equipments = equipments.none()
    if len(pin_status_params) > 0:
        equipments = equipments.filter(status__in=pin_status_params)
    else:
        equipments = equipments.none()
    # if city_id:
    #     equipments = equipments.filter(city__id=city_id)
    pins = [equipment.to_dict() for equipment in equipments]

    if len(fiber_status_params) > 0:
        fiber_lines = fiber_lines.filter(status__in=fiber_status_params)
    else:
        fiber_lines = fiber_lines.none()
    # if city_id:
    #     fiber_lines = fiber_lines.filter(city__id=city_id)

    lines = []
    if fiber_lines.count() > 0:
        fiber_lines = fiber_lines

        fiber_list = []
        for fiber in fiber_lines:
            line = {
                'id': fiber.id,
                'color': fiber.operator.fiber_color,
            }
            fiber_list.append(line)
        lines = grab_fiberlines_data(fiber_list)
    return HttpResponse(
        json.dumps({
            'lines': lines,
            'count': len(lines),
            'pins': pins
        }),
        content_type='application/json'
    )


def find_lines(request, *args, **kwargs):
    lines = []
    keyword = request.GET.get('query')
    member = request.user
    agent = AgentProfile.objects.get(member=member)
    operator = agent.operator
    fibers = Fiber.objects.filter(name__icontains=keyword, operator=operator)
    for line in fibers:
        events = FiberEventData.objects.filter(fiber=line)
        if events.count() == 0:
            lines.append(line)

    # lines = Fiber.objects.filter(name__icontains=keyword, status=Fiber.PENDING, operator=operator, city=agent.city)
    suggestions = ['%s %s' % (line.id, line.name) for line in lines]
    response = {'suggestions': suggestions}
    response = json.dumps(response)
    return HttpResponse(response)


@login_required
def search(request, *args, **kwargs):
    from django.db.models import Q
    keyword = request.GET.get('query')
    member = request.user
    agent = AgentProfile.objects.get(member=member)
    operator = agent.operator
    agents = []
    equipment_qs = Pin.objects
    if member.is_superuser:
        fiberlines = Fiber.objects.filter(name__icontains=keyword)
        line_count = fiberlines.count()
        equipments = equipment_qs.filter(Q(client_name__icontains=keyword) | Q(site_code__icontains=keyword) |
                                         Q(client_code__icontains=keyword) | Q(name__icontains=keyword))
        equipment_count = equipments.count()
    else:
        fiberlines = Fiber.objects.filter(name__icontains=keyword, operator=operator)
        line_count = fiberlines.count()
        equipments = equipment_qs.filter(Q(client_name__icontains=keyword) | Q(site_code__icontains=keyword) |
                                         Q(client_code__icontains=keyword) | Q(name__icontains=keyword),
                                         operator=operator)
        equipment_count = equipments.count()
    agents = User.objects.filter(username__icontains=keyword)
    lines = [line.to_dict() for line in fiberlines[:10]]
    pins = [pin.to_dict() for pin in equipments[:10]]
    for agent in agents:
        technician = {
            'id': agent.id,
            'username': agent.username,
        }
        agents.append(technician)
    response = {
        'lines': lines,
        'line_count': line_count,
        'pins': pins,
        'pins_count': equipment_count,
        'agents': agents
    }
    response = json.dumps(response)
    return HttpResponse(response)


@login_required
def load_equipments_by_city(request, *args, **kwargs):
    keyword = request.GET.get('query')
    member = request.user
    agent = AgentProfile.objects.get(member=member)
    operator = agent.operator
    agents = []
    if member.is_superuser:
        fiberlines = Fiber.objects.filter(name__icontains=keyword)
        line_count = fiberlines.count()
        equipments = Pin.objects.filter(name__icontains=keyword)
        equipment_count = equipments.count()
    else:
        fiberlines = Fiber.objects.filter(name__icontains=keyword, operator=operator)
        line_count = fiberlines.count()
        equipments = Pin.objects.filter(name__icontains=keyword, operator=operator)
        equipment_count = equipments.count()
    agents = User.objects.filter(username__icontains=keyword)
    lines = [line.to_dict() for line in fiberlines[:10]]
    pins = [pin.to_dict() for pin in equipments[:10]]
    for agent in agents:
        technician = {
            'id': agent.id,
            'username': agent.username,
        }
        agents.append(technician)
    response = {
        'lines': lines,
        'line_count': line_count,
        'pins': pins,
        'pins_count': equipment_count,
        'agents': agents
    }
    response = json.dumps(response)
    return HttpResponse(response)


@login_required
def get_selected_pin(request, *args, **kwargs):
    keyword = request.GET.get('pinId')
    equipments = Pin.objects.get(id=keyword)
    pins = equipments.to_dict()
    response = {
        'pins': pins
    }
    response = json.dumps(response)
    return HttpResponse(response)


@permission_required('pinsview.change_pin')
def change_pin_position(request, *args, **kwargs):
    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')
    pin_id = request.GET.get('pinId')
    pin = Pin.objects.get(id=pin_id)
    current_user = request.user
    agent = pin.agent
    if current_user == agent.member or current_user.is_superuser:
        pin.latitude = latitude
        pin.longitude = longitude
        pin.save()
        pin = {
            'id': pin.id,
            'lat': pin.latitude,
            'lng': pin.longitude,
            'icon': pin.category.icon.url if pin.category.icon.name else '',
            'zoom': pin.category.zoom
        }
        return HttpResponse(
            json.dumps({'pin': pin}),
            content_type='application/json'
        )
    else:
        response = {
            'Error': "You don't have permission to update this pin"
        }
    response = json.dumps(response)
    return HttpResponse(response)


def get_selected_fiber(request, *args, **kwargs):
    keyword = request.GET.get('fiberId')
    fiber_line = Fiber.objects.get(id=keyword)
    fiber_events = FiberEventData.objects.filter(fiber=fiber_line)
    lines = []
    line_coords = []
    for event in fiber_events:
        color = event.fiber.operator.fiber_color
        if event.longitude != "0.0" and event.latitude != "0.0":
            line_point = {
                'latitude': event.latitude,
                'longitude': event.longitude,
                'name': event.fiber.name,
                'description': event.fiber.description,
                'color': color,
            }
            line_coords.append(line_point)
        line = {'fiberline': fiber_line, 'line_coords': line_coords}
        lines.append(line)
    return HttpResponse(
        json.dumps({'lines': lines}),
        content_type='application/json'
    )


def get_agent_installation(request, *args, **kwargs):
    member = request.user
    agent = AgentProfile.objects.get(member=member)
    operator = agent.operator

    agent_id = request.GET.get('agentId')

    agent = AgentProfile.objects.get(id=agent_id)
    equipments = Pin.objects.filter(agent=agent, operator=operator)

    fiber_lines = Fiber.objects.filter(agent=agent, operator=operator)
    pins = [equipment.to_dict() for equipment in equipments]
    lines = []
    if fiber_lines.count() > 0:
        fiber_list = []
        for fiber in fiber_lines:
            line = {
                'id': fiber.id,
                'color': fiber.operator.fiber_color,
            }
            fiber_list.append(line)
        lines = grab_fiberlines_data(fiber_list)

    return HttpResponse(
        json.dumps({
            'lines': lines,
            'pins': pins
        }),
        content_type='application/json'
    )


def get_recent_equipments(request, *args, **kwargs):
    member = request.user
    agent = AgentProfile.objects.get(member=member)
    operator = agent.operator

    string_date = request.GET.get('stringDate')
    equipments = Pin.objects.filter(operator=operator).order_by('-updated_on')

    if request.GET.get('agentId'):
        agent_id = request.GET.get('agentId')
        agent = User.objects.get(id=agent_id)
        equipments.filter(agent=agent)
    if string_date:
        dates_list = retrieve_dates_from_interval(string_date)
        string_start_date = dates_list[0]
        string_end_date = dates_list[1]
        start_date = datetime.strptime(string_start_date, '%d-%m-%Y').date()
        end_date = datetime.strptime(string_end_date, '%d-%m-%Y').date()
        if start_date and end_date:
            equipments = equipments.filter(Q(updated_on__gte=start_date) & Q(updated_on__lt=end_date))
        elif start_date and not end_date:
            now = datetime.now()
            end_date = time.mktime(now.timetuple())
            equipments = equipments.filter(Q(updated_on__gte=start_date) & Q(updated_on__lt=end_date))
        elif end_date and not start_date:
            end_date_time = datetime.strptime(string_end_date, '%d-%m-%Y')
            end_date_dt = datetime(end_date_time.year, end_date_time.month, end_date_time.day, 0)
            start_date = int(time.mktime(end_date_dt.timetuple()))
            equipments = equipments.filter(Q(updated_on__gte=start_date) & Q(updated_on__lt=end_date))

    pins = [equipment.to_dict() for equipment in equipments]
    fiber_lines = Fiber.objects.filter(operator=operator).order_by('-updated_on')

    if request.GET.get('agentId'):
        agent_id = request.GET.get('agentId')
        agent = User.objects.get(id=agent_id)
        fiber_lines.filter(agent=agent)
    lines = []
    if fiber_lines.count() > 0:
        if string_date:
            dates_list = retrieve_dates_from_interval(string_date)
            string_start_date = dates_list[0]
            string_end_date = dates_list[1]
            start_date = datetime.strptime(string_start_date, '%d-%m-%Y').date()
            end_date = datetime.strptime(string_end_date, '%d-%m-%Y').date()
            if start_date and end_date:
                fiber_lines = fiber_lines.filter(Q(updated_on__gte=start_date) & Q(updated_on__lt=end_date))
            elif start_date and not end_date:
                now = datetime.now()
                end_date = time.mktime(now.timetuple())
                fiber_lines = fiber_lines.filter(Q(updated_on__gte=start_date) & Q(updated_on__lt=end_date))
            elif end_date and not start_date:
                end_date_time = datetime.strptime(string_end_date, '%d-%m-%Y')
                end_date_dt = datetime(end_date_time.year, end_date_time.month, end_date_time.day, 0)
                start_date = int(time.mktime(end_date_dt.timetuple()))
                fiber_lines = fiber_lines.filter(Q(updated_on__gte=start_date) & Q(updated_on__lt=end_date))
        fiber_list = []
        for fiber in fiber_lines:
            line = {
                'id': fiber.id,
                'color': fiber.operator.fiber_color,
            }
            fiber_list.append(line)
        lines = grab_fiberlines_data(fiber_list)
    return HttpResponse(
        json.dumps({
            'lines': lines,
            'pins': pins
        }),
        content_type='application/json'
    )


def grab_fibers(request, *args, **kwargs):
    member = request.user
    agent = AgentProfile.objects.get(member=member)
    operator = agent.operator
    start = int(request.GET.get('start', 0))
    length = 50
    limit = start + length
    fiber_list = []
    user_cities = agent.city.all()
    default_city = City.objects.get(name='YAOUNDE')
    if user_cities.count() > 0:
        user_city = user_cities[0]
    else:
        user_city = default_city
    if request.user.is_superuser:
        fiber_lines = Fiber.objects.filter(distance__gt=0).order_by('-id')[start:limit]
    else:
        fiber_lines = Fiber.objects.filter(operator=operator, city=user_city, distance__gt=0).order_by('id')[
                      start:limit]
        # fiber_lines = Fiber.objects.filter(operator=operator).order_by('id')[start:limit]

    for fiber in fiber_lines:
        line = {
            'id': fiber.id,
            'color': fiber.operator.fiber_color,
        }
        fiber_list.append(line)

    lines = grab_fiberlines_data(fiber_list)

    return HttpResponse(
        json.dumps(lines),
        content_type='application/json'
    )


@login_required
def grab_pins(request, *args, **kwargs):
    member = request.user
    try:
        agent = AgentProfile.objects.select_related().get(member=member)
    except:
        agent = None
    start = int(request.GET.get('start', 0))
    length = 50
    limit = start + length
    pins = []
    if agent and not request.user.is_staff:
        pin_queryset = Pin.objects.select_related().filter(agent=agent).order_by('id')[start:limit]
    else:
        pin_queryset = Pin.objects.select_related().all().order_by('-id')[start:limit]
    for pin in pin_queryset:
        category = pin.category
        equipment = {
            'id': pin.id,
            'lat': float(pin.latitude),
            'lng': float(pin.longitude),
            'icon': category.icon.url if category.icon.name else '',
            'zoom': category.zoom
        }
        pins.append(equipment)

    return HttpResponse(
        json.dumps(pins),
        content_type='application/json'
    )


def grab_offline_pins(request, *args, **kwargs):
    pins = []

    cat1 = PinCategory.objects.first()
    cat2 = [cat for cat in PinCategory.objects.all()][1]
    total_cat1_count = Pin.objects.filter(category=cat1).count()
    offline_cat1_count = Pin.objects.filter(status='offline', category=cat1).count()
    offline_cat2_count = Pin.objects.filter(status='offline', category=cat2).count()
    total_cat2_count = Pin.objects.filter(category=cat2).count()
    pin_queryset = Pin.objects.select_related('category', 'zone', 'agent', 'operator')\
        .filter(status='offline').order_by('-id')
    for pin in pin_queryset:
        category = pin.category
        if pin.city:
            city = to_dict(pin.city)
        else:
            city = City.objects.all()[0]
            city = to_dict(city)
        equipment = {
            'id': pin.id,
            'lat': float(pin.latitude),
            'lng': float(pin.longitude),
            'name': pin.name,
            'city': city,
            'zone': pin.zone.to_dict() if pin.zone else None,
            'zoom': category.zoom,
            'icon': category.icon.url if category.icon.name else '',
            'category': category.name.lower()
        }
        if equipment['lat'] >=0 or equipment['lng'] >=0:
            pins.append(equipment)
    return HttpResponse(json.dumps({
        'pins': pins,
        'total_pon_modem_count': total_cat1_count,
        'offline_pon_modem_count': offline_cat1_count,
        'offline_cat2_count': offline_cat2_count,
        'total_cat2_count': total_cat2_count,
    }), content_type='application/json')


@login_required
def grab_pin_info(request, *args, **kwargs):
    pin_id = request.GET.get('pinId')
    pin = Pin.objects.get(pk=pin_id)
    photo = pin.photo.url if pin.photo.name else getattr(settings, 'STATIC_URL') + 'img/no_photo.png'
    equipment = {
        'id': pin.id,
        'name': pin.name,
        'photo': photo,
        'created_on': pin.get_display_date(),
        'agent': pin.get_agent_name(),
        'description': pin.description,
        'admin_url': pin.get_admin_url(),
        'category': pin.category.name
    }
    return HttpResponse(
        json.dumps({"pin": equipment}),
        content_type='application/json'
    )


def grab_fiber_info(request, *args, **kwargs):
    fiber_id = request.GET.get('fiberId')
    fiber = Fiber.objects.get(pk=fiber_id)
    fiber = {
        'id': fiber.id,
        'name': fiber.name,
        'created_on': fiber.get_display_date(),
        'agent': fiber.get_agent_name(),
        'description': fiber.get_description(),
        'admin_url': fiber.get_admin_url(),
        'distance': fiber.distance
    }
    return HttpResponse(
        json.dumps({"fiber": fiber}),
        content_type='application/json'
    )


def grab_fiberlines_data(fiber_lines):
    lines = []
    for fiber_line in fiber_lines:
        current_fiber = Fiber.objects.get(pk=fiber_line['id'])
        fiber_events = FiberEventData.objects.filter(fiber=current_fiber)
        line_coords = []
        for event in fiber_events:
            if event.longitude != "0.0" and event.latitude != "0.0":
                line_point = {
                    'latitude': event.latitude,
                    'longitude': event.longitude,
                }
                line_coords.append(line_point)
        line = {'fiberline': fiber_line, 'line_coords': line_coords}
        lines.append(line)
    return lines


@permission_required("pinsview.change_fiber")
def update_fibers_distance(request, *args, **kwargs):
    fiber_id = request.GET.get('fiberId')
    distance = request.GET.get('distance')
    fiber = Fiber.objects.get(pk=fiber_id)
    fiber.distance = distance
    fiber.save()
    return HttpResponse(
        json.dumps({"success": True}),
        content_type='application/json'
    )


def check_new_fiber(request, *args, **kwargs):
    member = request.user
    agent = AgentProfile.objects.get(member=member)
    operator = agent.operator
    last_fiber_id = request.GET.get('lastFiberId')
    start = int(last_fiber_id)
    if not member.is_superuser:
        fiber_lines = Fiber.objects.filter(id__gt=start, operator=operator).order_by('-id')
    else:
        fiber_lines = Fiber.objects.filter(id__gt=start).order_by('-id')

    fiber_list = []
    for fiber in fiber_lines:
        line = {
            'id': fiber.id,
            'color': fiber.operator.fiber_color,
        }
        fiber_list.append(line)
    lines = grab_fiberlines_data(fiber_list)
    return HttpResponse(
        json.dumps(lines),
        content_type='application/json'
    )


@login_required
def get_specific_fiber_data(request, *args, **kwargs):
    member = request.user
    agent = AgentProfile.objects.get(member=member)
    operator = agent.operator
    last_fiber_id = request.GET.get('lastFiberId')
    fiber_id = request.GET.get('fiberId')
    if not member.is_superuser:
        fiber_line = Fiber.objects.get(id=fiber_id, operator=operator)
    else:
        fiber_line = Fiber.objects.get(id=fiber_id)
    lines = []

    fiber_events = FiberEventData.objects.filter(fiber=fiber_line)
    line_coords = []
    for event in fiber_events:
        color = event.fiber.operator.fiber_color
        fiber_line.color = color
        if event.longitude != "0.0" and event.latitude != "0.0":
            line_point = {
                'latitude': event.latitude,
                'longitude': event.longitude,
            }
            line_coords.append(line_point)
    line = {'fiberline': fiber_line.to_dict(), 'line_coords': line_coords}
    lines.append(line)

    return HttpResponse(
        json.dumps(lines),
        content_type='application/json'
    )


@login_required
def get_specific_pin_data(request, *args, **kwargs):
    pin_id = request.GET.get('pinId')
    pin_qs = Pin.objects.get(id=pin_id)
    pins = []
    category = pin_qs.category
    pin = {
        'id': pin_qs.id,
        'desc': pin_qs.description,
        'lat': float(pin_qs.latitude),
        'lng': float(pin_qs.longitude),
        'icon': category.icon.url if category.icon.name else '',
        'zoom': category.zoom
    }
    pins.append(pin)

    return HttpResponse(
        json.dumps(pins),
        content_type='application/json'
    )


@login_required
def check_new_pin(request, *args, **kwargs):
    member = request.user
    agent = AgentProfile.objects.get(member=member)
    last_pin_id = request.GET.get('lastPinId')
    if last_pin_id:
        pins = []
        if request.user.is_superuser:
            pin_queryset = Pin.objects.filter(id__gt=last_pin_id).order_by('-id')
        else:
            pin_queryset = Pin.objects.filter(agent=agent, id__gt=last_pin_id).order_by('-id')
        for pin in pin_queryset:
            category = pin.category
            pin = {
                'id': pin.id,
                'lat': float(pin.latitude),
                'lng': float(pin.longitude),
                'icon': category.icon.url if category.icon.name else '',
                'zoom': category.zoom
            }
            pins.append(pin)

        return HttpResponse(
            json.dumps(pins),
            content_type='application/json'
        )
    return HttpResponse(
        json.dumps([]), content_type='application/json'
    )


@login_required
def check_data_integrity(request, *args, **kwargs):
    online_fiber_ids = []
    online_pin_ids = []
    member = request.user
    agent = AgentProfile.objects.get(member=member)
    operator = agent.operator
    if member.is_superuser:
        online_fibers = Fiber.objects.all()
        online_pins = Pin.objects.all()
    else:
        online_fibers = Fiber.objects.filter(operator=operator)
        online_pins = Pin.objects.filter(operator=operator)
    if online_pins.count() > 0:
        last_pin_id = online_pins.order_by('-id')[0]
        pin_table_range = list(range(1, (last_pin_id.id + 1)))
        for pin in online_pins:
            online_pin_ids.append(pin.id)
        deleted_pins = [x for x in pin_table_range if x not in online_pin_ids]
    else:
        deleted_pins = []
    if online_fibers.count() > 0:
        last_fiber_id = online_fibers.order_by('-id')[0]
        fiber_table_range = list(range(1, (last_fiber_id.id + 1)))
        for fiber in online_fibers:
            online_fiber_ids.append(fiber.id)
        deleted_fibers = [x for x in fiber_table_range if x not in online_fiber_ids]
    else:
        deleted_fibers = []

    return HttpResponse(
        json.dumps({
            'deleted_pins': deleted_pins,
            'deleted_fibers': deleted_fibers
        }),
        content_type='application/json'
    )


@login_required
def check_line_update(request, *args, **kwargs):
    fiberIds = request.GET.get('fiberIds')
    if len(fiberIds) > 0:
        fiber_Id_list = fiberIds.split(',')
        fiberlines = []

        for id in fiber_Id_list:
            try:
                fiber = Fiber.objects.get(id=id)
            except Fiber.DoesNotExist:
                pass
            else:
                fiberlines.append(fiber)
        lines = []
        for fiber_line in fiberlines:
            fiber_events = FiberEventData.objects.filter(fiber=fiber_line)
            line_coords = []
            for event in fiber_events:
                color = event.fiber.operator.fiber_color
                fiber_line.color = color
                if event.longitude != "0.0" and event.latitude != "0.0":
                    line_point = {
                        'latitude': event.latitude,
                        'longitude': event.longitude,
                    }
                    line_coords.append(line_point)
            if len(line_coords) > 0:
                line = {'fiberline': fiber_line.to_dict(), 'line_coords': line_coords}
                lines.append(line)
        return HttpResponse(
            json.dumps(lines),
            content_type='application/json'
        )

    return HttpResponse(
        json.dumps({'lines': ''}),
        content_type='application/json'
    )


@login_required
def get_updated_fibers(request, *args, **kwargs):
    last_log_updated_id = request.GET.get('updated_ond_log_id')
    fiber_content_type = ContentType.objects.get(model='fiber')
    if last_log_updated_id:
        updated_fiber_logs = LogEntry.objects.filter(content_type=fiber_content_type,
                                                     id__gt=last_log_updated_id, action_flag=2).order_by('-id')
    else:
        updated_fiber_logs = LogEntry.objects.filter(content_type=fiber_content_type, action_flag=2).order_by('-id')

    if updated_fiber_logs.count() > 0:
        last_log_updated_id = updated_fiber_logs[0].id

    updated_fibers_list = []
    updated_fibers_pk_list = set()
    for fiber_log in updated_fiber_logs:
        updated_fibers_pk_list.add(fiber_log.object_id)

    for pk in updated_fibers_pk_list:
        try:
            fiber = Fiber.objects.get(pk=pk)
        except Fiber.DoesNotExist:
            pass
        else:
            updated_fibers_list.append(fiber)
    lines = []
    for fiber_line in updated_fibers_list:
        fiber_events = FiberEventData.objects.filter(fiber=fiber_line)
        line_coords = []
        color = fiber_line.operator.fiber_color
        fiber_line.color = color
        for event in fiber_events:
            if event.longitude != "0.0" and event.latitude != "0.0":
                line_point = {
                    'latitude': event.latitude,
                    'longitude': event.longitude,
                }
                line_coords.append(line_point)
        if len(line_coords) > 0:
            line = {'fiberline': fiber_line.to_dict(), 'line_coords': line_coords}
            lines.append(line)
    return HttpResponse(
        json.dumps({
            'lines': lines,
            'last_log_updated_id': last_log_updated_id
        }), content_type='application/json'
    )


def create_user_profile(request, *args, **kwargs):

    return HttpResponse(
        json.dumps({
            'Success': 'done'
        }), content_type='application/json'
    )


def migrate_equipments(request, *args, **kwargs):
    categories = PinCategory.objects.all()
    pins = Pin.objects.all()
    fibers = Fiber.objects.all()
    fiber_events = FiberEventData.objects.all()
    operators = Operator.objects.all()
    groups = Group.objects.all()
    users = User.objects.all()
    zones = Zone.objects.all()
    cities = City.objects.all()
    profiles = AgentProfile.objects.all()
    for event in fiber_events:
        latitude = event.latitude
        longitude = event.longitude
        created_on = event.created_on
        fiber = event.fiber
        try:
            mongo_fiber = Fiber.objects.using('maps').get(name=fiber.name)
        except Fiber.MultipleObjectsReturned:
            fs = Fiber.objects.using('maps').filter(name=fiber.name)
            for f in fs:
                agent = f.agent
                if agent.member.username == 'default':
                    f.delete(using='maps')
        else:
            mongo_fiber = Fiber.objects.using('maps').get(name=fiber.name)
        ev = FiberEventData(latitude=latitude, longitude=longitude, created_on=created_on, fiber=mongo_fiber)
        ev.save(using='maps')

    return HttpResponse(
        json.dumps({
            'Success': True,
        }), content_type='application/json'
    )


def update_equipments_city(request, *args, **kwargs):
    pins = Pin.objects.all()
    fibers = Fiber.objects.all()
    for pin in pins:
        if pin.agent.city:
            pin.city = pin.agent.city
        else:
            city = City.objects.get(name='Yaounde')
            pin.city = city
        pin.save()

    for fiber in fibers:
        if fiber.agent and fiber.agent.city:
            fiber.city = fiber.agent.city[0]
        else:
            city = City.objects.get(name='Yaounde')
            fiber.city = city
        fiber.save()

    return HttpResponse(
        json.dumps({
            'Success': True,
        }), content_type='application/json'
    )


def update_equips(request, *args, **kwargs):
    pins = Pin.objects.all()
    fibers = Fiber.objects.all()
    for pin in pins:
        agent = pin.agent
        pin.profile = AgentProfile.objects.get(member=agent)
        pin.save()

    for fiber in fibers:
        agent = fiber.agent
        fiber.profile = AgentProfile.objects.get(member=agent)
        fiber.save()

    return HttpResponse(
        json.dumps({
            'Success': True,
        }), content_type='application/json'
    )


def update_equi(request, *args, **kwargs):
    pins = Pin.objects.all()
    operator = Operator.objects.all()[0]
    for pin in pins:
        pin.operator = operator
        pin.save()
    return HttpResponse(
        json.dumps({
            'Success': True,
        }), content_type='application/json'
    )


def update_pin_city(request, *args, **kwargs):
    pins_qs = Pin.objects.all()
    city = City.objects
    for pin in pins_qs:
        longitude = float(pin.longitude)
        latitude = float(pin.latitude)
        if 9.00 < longitude < 10.0 and 3.0 < latitude <= 5.0:
            c = city.get(name='Douala')
            pin.city = c
            pin.save()
    return HttpResponse(
        json.dumps({
            'Success': True,
        }), content_type='application/json'
    )


def update_fiber_city(request, *args, **kwargs):
    fibers_qs = Fiber.objects.all()
    for fiber in fibers_qs:
        first_event_data = FiberEventData.objects.filter(fiber=fiber)
        if first_event_data.count() <= 0:
            continue
        longitude = float(first_event_data[0].longitude)
        latitude = float(first_event_data[0].latitude)
        if longitude == "0.0":
            continue
        if 9 <= longitude < 10 and 3 <= latitude <= 5:
            c = City.objects.get(name='Douala')
            fiber.city = c
            fiber.save()
        elif 11 <= longitude < 12 and 3 <= latitude <= 5:
            c = City.objects.get(name='Yaounde')
            fiber.city = c
            fiber.save()
    return HttpResponse(
        json.dumps({
            'Success': True,
        }), content_type='application/json'
    )


def load_modems():
    try:
        PinCategory.objects.get(name='Modem')
    except PinCategory.DoesNotExist:
        PinCategory.objects.create(name='Modem')
    category = PinCategory.objects.get(name='Modem')
    member = User.objects.get(username='joseph.mbock@gmail.com')
    agent = AgentProfile.objects.get(member=member)
    operator = Operator.objects.get(name="Creolink Communications")
    maps_files = '/home/roddy/Desktop/maps_json.txt'

    with open(maps_files) as f:
        data = json.load(f)

    for modem in data["features"]:
        latitude = modem["geometry"]["coordinates"][0]
        longitude = modem["geometry"]["coordinates"][1]
        client_name = modem["properties"]["matchcode"]
        status = modem["properties"]["status"]
        client_code = modem["properties"]["cat2_id"]
        description = modem["properties"]["cat2_mac"] + " / " + modem["properties"]["matchcode"]
        name = 'Modem' + client_code
        pin = Pin(latitude=latitude, longitude=longitude, client_code=client_code, status=status,
                        description=description, client_name=client_name, name=name, category=category, agent=agent,
                        operator=operator)
        if 9 <= longitude < 10 and 3 <= latitude <= 5:
            c = City.objects.get(name='Douala')
            pin.city = c
            pin.save()
        elif 11 <= longitude < 12 and 3 <= latitude <= 5:
            c = City.objects.get(name='Yaounde')
            pin.city = c
        pin.save()


@login_required
def get_asset_event_log(request, *args, **kwargs):
    asset_pk = request.GET.get('assetId')
    asset_logs = AssetLog.objects.filter(asset_id=asset_pk).order_by('created_on')
    log_events = []
    for log in asset_logs:
        event = {
            'id': log.id,
            'title': log.name,
            'type': log.log_event_type.name,
            'details': log.details,
            'agent': log.agent.member.username,
            'summary': log.details[0:80],
            'created': log.get_created_on(),
        }
        log_events.append(event)
    return HttpResponse(
        json.dumps({"event_list": log_events}),
        content_type='application/json'
    )


@csrf_exempt
@login_required
def save_asset_config(request, *args, **kwargs):
    data = json.loads(request.body)
    asset_id = data['asset_id']
    asset_configs = data['details']
    asset = Pin.objects.get(pk=asset_id)
    asset.configuration = json.dumps(asset_configs)
    asset.save()
    return HttpResponse(
        json.dumps({"success": True}),
        content_type='application/json'
    )


@permission_required("pinsview.add_pin_log")
def save_event_log(request, *args, **kwargs):
    details = request.GET.get('details')
    log_event_type_id = request.GET.get('log_event_type_id')
    asset_type = request.GET.get('assetType')
    asset_id = request.GET.get('asset_id')
    name = request.GET.get('name')
    try:
        Pin.objects.get(pk=asset_id)
    except Pin.DoesNotExist:
        asset_type = AssetLog.FIBER
    else:
        asset_type = AssetLog.PIN
    log_event_type = LogEventType.objects.get(pk=log_event_type_id)
    agent = AgentProfile.objects.get(member=request.user)
    event_log = AssetLog(log_event_type=log_event_type, asset_id=asset_id, asset_type=asset_type, details=details,
                         agent=agent, name=name)
    event_log.save()
    event = {
        'id': event_log.id,
        'type': event_log.log_event_type.name,
        'details': event_log.details,
        'created': event_log.get_created_on(),
        'summary': event_log.details[0:80],
    }
    return HttpResponse(json.dumps({'event_log': event}), )


@permission_required("pinsview.add_pin_log")
def grab_event_log_detail(request, *args, **kwargs):
    log_pk = request.GET.get('logId')
    event_log = AssetLog.objects.get(pk=log_pk)
    event = {
        'id': event_log.id,
        'type': event_log.log_event_type.name,
        # 'measure': event_log.measure,
        'details': event_log.details,
        'event_type_label': event_log.log_event_type.measure_label,
        'created_on': event_log.get_created_on,
    }
    return HttpResponse(json.dumps({"event": event}), content_type='application/json')


@csrf_exempt
@permission_required("pinsview.add_pin_log")
def grab_asset_config(request, *args, **kwargs):
    asset_id = request.GET.get('assetId')
    pin = Pin.objects.get(pk=asset_id)
    if not pin.configuration:
        return HttpResponse(json.dumps({"no_config": True}), content_type='application/json')
    return HttpResponse(pin.configuration, content_type='application/json')


def grab_neighborhoods_from_zones(zones):
    neighborhood_list = []
    for zone in zones:
        neighborhoods = Neighborhood.objects.filter(zone=zone)
        if len(neighborhoods) > 0:
            for neighborhood in neighborhoods:
                neighborhood_list.append(neighborhood)
    return neighborhood_list


def update_pin_cities(request):
    pins = Pin.objects.all()
    for pin in pins:
        longitude = float(pin.longitude)
        latitude = float(pin.latitude)
        c = City.objects.get(name='YAOUNDE')
        if longitude >= 11.41138 and longitude < 11.7306 and latitude >= 3.73738 and latitude < 4.0525:
            c = City.objects.get(name='YAOUNDE')
        elif longitude >= 9.06281 and longitude < 9.8382 and latitude >= 3.9490 and latitude < 4.1312:
            c = City.objects.get(name='DOUALA')
        elif longitude >= 9.0925 and longitude < 9.3308 and latitude >= 3.9579 and latitude < 4.1121:
            c = City.objects.get(name='LIMBE')
        elif longitude >= 8.9202 and longitude < 9.4860 and latitude >= 4.0963 and latitude < 4.4640:
            c = City.objects.get(name='BUEA')
        elif longitude >= 9.8267 and longitude < 10.8470 and latitude >= 2.3496 and latitude < 3.2536:
            c = City.objects.get(name='KRIBI')
        elif longitude >= 13.3354 and longitude < 14.3764 and latitude >= 3.8925 and latitude < 5.1164:
            c = City.objects.get(name='BERTOUA')
        elif longitude >= 13.0470 and longitude < 13.9534 and latitude >= 8.9836 and latitude < 9.8090:
            c = City.objects.get(name='GAROUA')
        elif longitude >= 13.7773 and longitude < 14.8982 and latitude >= 10.2076 and latitude < 10.9798:
            c = City.objects.get(name='MAROUA')
        elif longitude >= 12.9765 and longitude < 14.5983 and latitude >= 6.6951 and latitude < 7.7373:
            c = City.objects.get(name='NGAOUNDERE')
        elif longitude >= 10.0621 and longitude < 10.8325 and latitude >= 5.1439 and latitude < 5.6479:
            c = City.objects.get(name='BAFOUSSAM')
        elif longitude >= 9.8334 and longitude < 10.5592 and latitude >= 5.8013 and latitude < 6.3393:
            c = City.objects.get(name='BAMENDA')
        elif longitude >= 9.6637 and longitude < 10.5371 and latitude >= 3.2623 and latitude < 3.9777:
            c = City.objects.get(name='EDEA')
        pin.city = c
        pin.save()


def save_prospect(request, *args, **kwargs):
    # todo
    offline_url = settings.OFFLINE_URL
    member = User.objects.get(username='system')
    category = PinCategory.objects.get(name='Prospect from sales')
    operator = Operator.objects.get(name='Creolink Communications')
    agent = AgentProfile.objects.get(member=member)
    operator = operator
    agent = agent
    category = category
    latitude = request.GET.get('lat')
    longitude = request.GET.get('lng')
    client_name = request.GET.get('customer_name')
    order_id = request.GET.get('order_id')
    order_name = client_name
    description = '%s - %s' % (order_name, order_id)
    if not latitude or not longitude or not order_id:
        return HttpResponse("Few fields not found; we can allow the save of a pin without some data", content_type="text/plain")
    pin = Pin(operator=operator, agent=agent, category=category, latitude=latitude, longitude=longitude, description=description)
    pin.save()
    pin_url = "%s/equipments?pin_id=%s&lat=%s&lng=%s" % (offline_url, pin.id, latitude, longitude)
    if not request.GET.get('debug'):
        pin_url = "http://maps.creolink.com/equipments?pin_id=%s&lat=%s&lng=%s" % (pin.id, latitude, longitude)
    pin.name = 'Prospect_from_sales_%s' % pin.id
    pin.save()
    return HttpResponse(pin_url, content_type="text/plain")


def update_prospect_status(request, *args, **kwargs):
    pin_category = PinCategory.objects.get(name='Client')
    prospect_category = PinCategory.objects.get(name='Prospect from sales')
    pin_id = request.GET.get('pin_id')
    try:
        pin = Pin.objects.get(pk=pin_id)
    except Pin.DoesNotExist:
        return HttpResponse('Pin does not exist', content_type="text/plain")
    except:
        return HttpResponse('Unknown error occured', content_type="text/plain")

    if pin.category != prospect_category:
        return HttpResponse('Pin does not exists', content_type="text/plain")
    pin.category = pin_category
    pin.name = 'Client_from_sales_%s' %pin.id
    pin.save()
    return HttpResponse('Pin successfully updated', content_type="text/plain")



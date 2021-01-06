# coding=utf-8
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import gettext_lazy as _
from datetime import datetime


from django.forms import ModelForm, Textarea
from django.utils import translation, timezone

from ikwen.accesscontrol.models import Member
from ikwen.core.models import Model
from ikwen.core.utils import to_dict


class Province(Model):
    name = models.CharField(max_length=50)
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)

    def __unicode__(self):
        return self.name


class Division(Model):
    name = models.CharField(max_length=50)
    province = models.ForeignKey(Province)
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)

    def __unicode__(self):
        return self.name


class SubDivision(Model):
    name = models.CharField(max_length=50)
    division = models.ForeignKey(Division)
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)

    def __unicode__(self):
        return self.name


class City(Model):
    name = models.CharField(max_length=50)
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)
    default = models.BooleanField(default=False, help_text=_("If checked, the map will open on this city."
                                                             " NB: Only one city should be the default"))

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Cities'

    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        if self.default == True:
            if City.objects.filter(default=True).count() > 0:
                self.default = False
        return super(City, self).save()


class Zone(Model):
    name = models.CharField(max_length=50)
    city = models.ForeignKey(City)
    geo_fancing_coords = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=50, null=True, blank=True)
    sub_division = models.ForeignKey(SubDivision, null=True, blank=True)

    def __unicode__(self):
        return self.name


class Neighborhood(Model):
    name = models.CharField(max_length=50)
    zone = models.ForeignKey(Zone)
    latitude = models.FloatField(default=0.0)
    longitude = models.FloatField(default=0.0)

    def __unicode__(self):
        return self.name


class Operator(models.Model):
    BLUE_YDE_PARTNERS = "#417690"
    DARK_RED_DLA_PARTNERS = "#BF0072"
    RED = "#FF0000"
    GREEN = "#00FF00"
    BLUE = "#0000FF"
    BLACK = "#000000"
    YELLOW = "#FFFF00"
    AQUA = "#00FFFF"
    PINK = "#FF00FF"
    DARK_RED = "#850117"
    DARK_BLUE = "#300169"
    DARK_GREEN = "#197F5B"
    DARK = "#5b3f12"
    BROWN = "#280819"
    ORANGE = "#ff6600"
    COLOUR_CHOICES = (
        (BLUE_YDE_PARTNERS, "Blue for YDE partners"),
        (DARK_RED_DLA_PARTNERS, "Daerk red for DLA partners"),
        (RED, "Red"),
        (GREEN, "Green"),
        (BLUE, "Blue"),
        (BLACK, "Black"),
        (YELLOW, "Yellow"),
        (AQUA, "Aqua"),
        (PINK, "Pink"),
        (DARK_RED, "Dark red"),
        (DARK_BLUE, "Dark blue"),
        (DARK_GREEN, "Dark green"),
        (DARK, "Dark"),
        (BROWN, "Brown"),
        (ORANGE, "orange"),
    )
    name = models.CharField(max_length=100)
    fiber_color = models.CharField(max_length=7, choices=COLOUR_CHOICES)

    def __unicode__(self):
        return self.name


class AgentProfile(Model):
    member = models.OneToOneField(Member, null=True, blank=True)
    city = models.ManyToManyField(City, null=True, blank=True)
    zone = models.ManyToManyField(Zone, null=True, blank=True)
    operator = models.ForeignKey(Operator, null=True, blank=True)

    def __unicode__(self):
        return self.member.username


class Fiber(models.Model):
    PENDING = "Pending"
    VALIDATE = "Validate"

    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (VALIDATE, "Validate"),
    )

    start_point = models.CharField(max_length=240, blank=True)
    end_point = models.CharField(max_length=240, blank=True)
    name = models.CharField(max_length=255, blank=True)
    distance = models.FloatField(default=0.0)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=PENDING, editable=False)
    zone = models.ForeignKey(Zone, null=True, blank=True, editable=False)
    agent = models.ForeignKey(AgentProfile, null=True, blank=True)
    operator = models.ForeignKey(Operator, null=True, blank=True)
    city = models.ForeignKey(City, null=True, blank=True)
    neighborhood = models.ForeignKey(Neighborhood, null=True, blank=True)
    created_on = models.DateField(default=datetime.now())
    last_update = models.DateField(default=datetime.now())

    class Meta:
        unique_together = [("start_point", "end_point")]

    def __unicode__(self):
        return self.name

    def get_agent_name(self):
        if self.agent.member.first_name and self.agent.member.last_name:
            return "%s %s" % (self.agent.member.first_name, self.agent.member.last_name)
        elif self.agent.member.first_name and not self.agent.member.last_name:
            return "%s" % self.agent.member.first_name
        elif not self.agent.member.first_name and self.agent.member.last_name:
            return "%s" % self.agent.member.last_name
        elif not self.agent.member.first_name and not self.agent.member.last_name:
            return "%s" % self.agent.member.username

    def get_admin_url(self):
        return reverse('admin:%s_%s_change' % (self._meta.app_label, self._meta.model_name), args=[self.id])

    def get_display_date(self):
        return to_display_date(self.created_on)

    def to_dict(self):
        # zone = self.zone.to_dict()
        # agent = self.agent.member.get_full_name()
        var = to_dict(self)
        var['admin_url'] = self.get_admin_url()
        var['agent'] = self.agent.member.username if self.agent else "root"
        var['created'] = self.created_on.strftime("%Y-%m-%d")
        var['display_agent_name'] = self.get_agent_name()
        del (var['zone_id'])
        del (var['created_on'])
        del (var['last_update'])
        return var

    def save(self, *args, **kwargs):
        start_point = self.start_point.replace(' ', '_').replace(u'é', u'e').replace(u'è', u'e').replace(u'à', u'a')
        end_point = self.end_point.replace(' ', '_').replace(u'é', u'e').replace(u'è', u'e').replace(u'à', u'a')
        self.name = '%s-%s' % (start_point, end_point)
        super(Fiber, self).save(*args, **kwargs)

    def get_description(self):
        return self.description.replace("\n", ' ').replace("\r", '')


class FiberEventData(models.Model):
    fiber = models.ForeignKey(Fiber)
    longitude = models.CharField(max_length=240, default="0.0")
    latitude = models.CharField(max_length=240, default="0.0")
    created_on = models.DateField(default=timezone.now)

    def __unicode__(self):
        return self.fiber.name


class PinCategory(Model):
    name = models.CharField(max_length=240, blank=True)
    icon = models.ImageField(blank=True, upload_to="icons", default="icons/logo-pinsview-32x32.png")
    description = models.TextField(blank=True)
    zoom = models.IntegerField(default=13)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Pin categories'


class Pin(Model):
    ONLINE = "online"
    OFFLINE = "offline"
    STATUS_CHOICES = (
        (ONLINE, "online"),
        (OFFLINE, "offline"),
    )
    member = models.ForeignKey(Member, blank=True, null=True)
    category = models.ForeignKey(PinCategory)
    name = models.CharField(max_length=240, blank=True, null=True)
    longitude = models.CharField(max_length=240, default="0.0")
    latitude = models.CharField(max_length=240, default="0.0")
    formatted_address = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True)
    configuration = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default=ONLINE)
    zone = models.ForeignKey(Zone, blank=True, null=True)
    photo = models.ImageField(upload_to="pins", null=True, blank=True, default="pins/logo-pinsview.png")
    agent = models.ForeignKey(AgentProfile, null=True, blank=True)
    operator = models.ForeignKey(Operator, null=True, blank=True)
    city = models.ForeignKey(City, null=True, blank=True)
    neighborhood = models.ForeignKey(Neighborhood, null=True, blank=True)
    is_active = models.BooleanField(default=True, editable=False)

    def __unicode__(self):
        return self.name

    def get_agent_name(self):
        if self.agent:
            if self.agent.member.first_name and self.agent.member.last_name:
                return "%s %s" % (self.agent.member.first_name, self.agent.member.last_name)
            elif self.agent.member.first_name and not self.agent.member.last_name:
                return "%s" % self.agent.member.first_name
            elif not self.agent.member.first_name and self.agent.member.last_name:
                return "%s" % self.agent.member.last_name
            elif not self.agent.member.first_name and not self.agent.member.last_name:
                return "%s" % self.agent.member.username
        else:
            return "root"

    def get_admin_url(self):
        return reverse('%s:change_%s' % (self._meta.app_label, self._meta.model_name),
                       args=[self.id])

    def to_dict(self):
        var = to_dict(self)
        var['category'] = self.category.to_dict()
        var['image'] = self.photo.url if self.photo else None
        var['display_agent_name'] = self.get_agent_name()
        var['display_date'] = self.created_on.strftime("%Y-%m-%d")
        # del (var['photo'])
        # del (var['agent'])
        return var

    def get_description(self):
        return self.description.replace("\n", ' ').replace("\r", '')

    def get_display_date(self):
        return to_display_date(self.created_on)

    class Meta:
        verbose_name_plural = 'Pins'


class AddPinForm(ModelForm):
    class Meta:
        model = Pin
        widgets = {
            'description': Textarea(attrs={'cols': 80, 'rows': 50}),
        }
        fields = ['name', 'category', 'longitude', 'latitude']


def to_display_date(a_datetime):
    if translation.get_language().lower().find('en') == 0:
        display_date = '%02d/%02d, %d ' % (
            a_datetime.month, a_datetime.day, a_datetime.year
        )
    else:
        display_date = '%02d/%02d/%d' % (
            a_datetime.day, a_datetime.month, a_datetime.year
        )
    return display_date


class LogEventType(Model):
    name = models.CharField(max_length=240)
    measure_label = models.CharField(max_length=240, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Log Event types'


class AssetLog(Model):
    FIBER = "Fiber"
    PIN = "Pin"
    ASSET_CHOICES = (
        (FIBER, "Fiber"),
        (PIN, "Pin"),
    )
    name = models.CharField(max_length=240, null=True, blank=True)
    log_event_type = models.ForeignKey(LogEventType)
    asset_id = models.CharField(max_length=240)
    asset_type = models.CharField(max_length=240, choices=ASSET_CHOICES, default=PIN)
    details = models.TextField(blank=True)
    agent = models.ForeignKey(AgentProfile, null=True, blank=True)

    def __unicode__(self):
        return self.log_event_type.name

    def get_asset(self):
        try:
            asset = Pin.objects.get(pk=self.asset_id)
        except Pin.DoesNotExist:
            asset = Fiber.objects.get(pk=self.asset_id)
        return asset

    def get_created_on(self):
        if self.created_on:
            return self.created_on.strftime("%Y-%m-%d")
        return datetime.now().strftime("%Y-%m-%d")

    def to_dict(self):
        var = to_dict(self)
        var['asset'] = self.get_asset.to_dict()
        return var



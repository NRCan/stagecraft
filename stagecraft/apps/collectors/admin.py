from django import forms
from django.contrib import admin
from django.contrib.admin import widgets

from stagecraft.apps.collectors import models


@admin.register(models.Collector)
class CollectorAdmin(admin.ModelAdmin):
    class Media:
        js = ('admin/js/filterselect.js',)

    filter_horizontal = ('owners',)


@admin.register(models.DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    filter_horizontal = ('owners',)

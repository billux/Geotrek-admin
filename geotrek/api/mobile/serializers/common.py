from __future__ import unicode_literals
import os

from django.conf import settings
from drf_dynamic_fields import DynamicFieldsMixin
from rest_framework import serializers

from geotrek.common import models as common_models
from geotrek.flatpages import models as flatpage_models
from geotrek.trekking import models as trekking_models


if 'geotrek.zoning' in settings.INSTALLED_APPS:
    from geotrek.zoning import models as zoning_models

    class DistrictSerializer(serializers.ModelSerializer):
        class Meta:
            model = zoning_models.District
            fields = ('id', 'name')

    class CitySerializer(serializers.ModelSerializer):
        id = serializers.ReadOnlyField(source='code')

        class Meta:
            model = zoning_models.City
            fields = ('id', 'name')

if 'geotrek.tourism' in settings.INSTALLED_APPS:
    from geotrek.tourism import models as tourism_models

    class InformationDeskTypeSerializer(serializers.ModelSerializer):
        name = serializers.ReadOnlyField(source='label')
        pictogram = serializers.SerializerMethodField(read_only=True)

        def get_pictogram(self, obj):
            if not obj.pictogram:
                return None
            file_name, file_extension = os.path.splitext(str(obj.pictogram.url))
            return '{file}.png'.format(file=file_name) if file_extension == '.svg' else obj.pictogram.url

        class Meta:
            model = tourism_models.InformationDeskType
            fields = ('id', 'name', 'pictogram')

    class TouristicContentTypeSerializer(serializers.ModelSerializer):
        name = serializers.ReadOnlyField(source='label')
        pictogram = serializers.SerializerMethodField(read_only=True)

        def get_pictogram(self, obj):
            if not obj.pictogram:
                return None
            file_name, file_extension = os.path.splitext(str(obj.pictogram.url))
            return '{file}.png'.format(file=file_name) if file_extension == '.svg' else obj.pictogram.url

        class Meta:
            model = tourism_models.TouristicContentType
            fields = ('id', 'name', 'pictogram')

    class TouristicEventTypeSerializer(serializers.ModelSerializer):
        name = serializers.ReadOnlyField(source='type')
        pictogram = serializers.SerializerMethodField(read_only=True)

        def get_pictogram(self, obj):
            if not obj.pictogram:
                return None
            file_name, file_extension = os.path.splitext(str(obj.pictogram.url))
            return '{file}.png'.format(file=file_name) if file_extension == '.svg' else obj.pictogram.url

        class Meta:
            model = tourism_models.TouristicEventType
            fields = ('id', 'name', 'pictogram')

    class TouristicContentCategorySerializer(serializers.ModelSerializer):
        name = serializers.ReadOnlyField(source='label')
        pictogram = serializers.SerializerMethodField(read_only=True)

        def get_pictogram(self, obj):
            if not obj.pictogram:
                return None
            file_name, file_extension = os.path.splitext(str(obj.pictogram.url))
            return '{file}.png'.format(file=file_name) if file_extension == '.svg' else obj.pictogram.url

        class Meta:
            model = tourism_models.TouristicContentCategory
            fields = ('id', 'name', 'pictogram', 'type1_label', 'type2_label', 'color')


if 'geotrek.trekking' in settings.INSTALLED_APPS:
    class DifficultySerializer(DynamicFieldsMixin, serializers.ModelSerializer):
        name = serializers.ReadOnlyField(source='difficulty')
        pictogram = serializers.SerializerMethodField(read_only=True)

        def get_pictogram(self, obj):
            if not obj.pictogram:
                return None
            file_name, file_extension = os.path.splitext(str(obj.pictogram.url))
            return '{file}.png'.format(file=file_name) if file_extension == '.svg' else obj.pictogram.url

        class Meta:
            model = trekking_models.DifficultyLevel
            fields = ('id', 'name', 'pictogram')

    class PracticeSerializer(serializers.ModelSerializer):
        pictogram = serializers.SerializerMethodField(read_only=True)

        def get_pictogram(self, obj):
            file_name, file_extension = os.path.splitext(str(obj.pictogram.url))
            return '{file}.png'.format(file=file_name) if file_extension == '.svg' else obj.pictogram.url

        class Meta:
            model = trekking_models.Practice
            fields = ('id', 'name', 'slug', 'pictogram', 'color')

    class AccessibilitySerializer(serializers.ModelSerializer):
        pictogram = serializers.SerializerMethodField(read_only=True)

        def get_pictogram(self, obj):
            if not obj.pictogram:
                return None
            file_name, file_extension = os.path.splitext(str(obj.pictogram.url))
            return '{file}.png'.format(file=file_name) if file_extension == '.svg' else obj.pictogram.url

        class Meta:
            model = trekking_models.Accessibility
            fields = ('id', 'name', 'pictogram',)

    class RouteSerializer(serializers.ModelSerializer):
        name = serializers.ReadOnlyField(source='route')
        pictogram = serializers.SerializerMethodField(read_only=True)

        def get_pictogram(self, obj):
            if not obj.pictogram:
                return None
            file_name, file_extension = os.path.splitext(str(obj.pictogram.url))
            return '{file}.png'.format(file=file_name) if file_extension == '.svg' else obj.pictogram.url

        class Meta:
            model = trekking_models.Route
            fields = ('id', 'name', 'pictogram',)

    class ThemeSerializer(serializers.ModelSerializer):
        name = serializers.ReadOnlyField(source='label')
        pictogram = serializers.SerializerMethodField(read_only=True)

        def get_pictogram(self, obj):
            file_name, file_extension = os.path.splitext(str(obj.pictogram.url))
            return '{file}.png'.format(file=file_name) if file_extension == '.svg' else obj.pictogram.url

        class Meta:
            model = common_models.Theme
            fields = ('id', 'name', 'pictogram')

    class NetworkSerializer(serializers.ModelSerializer):
        name = serializers.ReadOnlyField(source='network')
        pictogram = serializers.SerializerMethodField(read_only=True)

        def get_pictogram(self, obj):
            if not obj.pictogram:
                return None
            file_name, file_extension = os.path.splitext(str(obj.pictogram.url))
            return '{file}.png'.format(file=file_name) if file_extension == '.svg' else obj.pictogram.url

        class Meta:
            model = trekking_models.TrekNetwork
            fields = ('id', 'name', 'pictogram')

    class POITypeSerializer(serializers.ModelSerializer):
        name = serializers.ReadOnlyField(source='label')
        pictogram = serializers.SerializerMethodField(read_only=True)

        def get_pictogram(self, obj):
            if not obj.pictogram:
                return None
            file_name, file_extension = os.path.splitext(str(obj.pictogram.url))
            return '{file}.png'.format(file=file_name) if file_extension == '.svg' else obj.pictogram.url

        class Meta:
            model = trekking_models.POIType
            fields = ('id', 'name', 'pictogram')


class FlatPageListSerializer(serializers.ModelSerializer):
    class Meta:
        model = flatpage_models.FlatPage
        fields = ('id', 'title')


class FlatPageDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = flatpage_models.FlatPage
        fields = ('id', 'title', 'content', 'external_url')

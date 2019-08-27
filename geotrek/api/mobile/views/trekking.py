from __future__ import unicode_literals

from django.conf import settings
from django.db.models import Count, F, Q, Prefetch
from django_filters.rest_framework.backends import DjangoFilterBackend

from geotrek.api.mobile.serializers import trekking as api_serializers_trekking
from geotrek.api.mobile.serializers import tourism as api_serializers_tourism

from geotrek.api.v2.functions import Transform, Length, StartPoint, EndPoint
from geotrek.trekking import models as trekking_models

from rest_framework_extensions.mixins import DetailSerializerMixin
from rest_framework.permissions import AllowAny
from rest_framework import response
from rest_framework import viewsets
from rest_framework import decorators

from geotrek.common.models import Attachment


class TrekViewSet(DetailSerializerMixin, viewsets.ReadOnlyModelViewSet):
    filter_backends = (DjangoFilterBackend,)
    serializer_class = api_serializers_trekking.TrekListSerializer
    serializer_detail_class = api_serializers_trekking.TrekDetailSerializer
    filter_fields = ('difficulty', 'themes', 'networks', 'practice')
    permission_classes = [AllowAny, ]

    def get_queryset(self, *args, **kwargs):
        lang = self.request.LANGUAGE_CODE
        queryset = trekking_models.Trek.objects.existing()\
            .select_related('topo_object') \
            .prefetch_related('topo_object__aggregations', 'themes', 'accessibilities') \
            .prefetch_related(Prefetch(
                'attachments',
                queryset=Attachment.objects.order_by('-starred', 'attachment_file'),
                to_attr='_all_attachments'
            )) \
            .order_by('pk').annotate(length_2d_m=Length('geom'))
        if not self.action == 'list':
            queryset = queryset.annotate(geom2d_transformed=Transform(F('geom'), settings.API_SRID))
        if self.action == 'list':
            queryset = queryset.annotate(count_parents=Count('trek_parents')) \
                .exclude(Q(count_parents__gt=0) & Q(published=False)) \
                .annotate(count_children=Count('trek_children'))
        if 'portal' in self.request.GET:
            queryset = queryset.filter(Q(portal__name__in=self.request.GET['portal'].split(',')) | Q(portal=None))
        return queryset.annotate(start_point=Transform(StartPoint('geom'), settings.API_SRID),
                                 end_point=Transform(EndPoint('geom'), settings.API_SRID)). \
            filter(Q(**{'published_{lang}'.format(lang=lang): True})
                   | Q(**{'trek_parents__parent__published_{lang}'.format(lang=lang): True,
                          'trek_parents__parent__deleted': False})).distinct()

    def get_serializer_context(self):
        return {'root_pk': self.request.GET.get('root_pk')}

    @decorators.detail_route(methods=['get'])
    def pois(self, request, *args, **kwargs):
        trek = self.get_object()
        root_pk = self.request.GET.get('root_pk') or trek.pk
        qs = trek.pois.filter(published=True).select_related('topo_object', 'type', )\
            .prefetch_related('topo_object__aggregations', 'attachments') \
            .annotate(geom2d_transformed=Transform(F('geom'), settings.API_SRID)) \
            .order_by('pk')
        data = api_serializers_trekking.POIListSerializer(qs, many=True, context={'root_pk': root_pk}).data
        return response.Response(data)

    @decorators.detail_route(methods=['get'])
    def touristic_contents(self, request, *args, **kwargs):
        trek = self.get_object()
        root_pk = self.request.GET.get('root_pk') or trek.pk
        qs = trek.touristic_contents.filter(published=True).prefetch_related('attachments') \
            .annotate(geom2d_transformed=Transform(F('geom'), settings.API_SRID)) \
            .order_by('pk')
        data = api_serializers_tourism.TouristicContentListSerializer(qs, many=True, context={'root_pk': root_pk}).data
        return response.Response(data)

    @decorators.detail_route(methods=['get'])
    def touristic_events(self, request, *args, **kwargs):
        trek = self.get_object()
        root_pk = self.request.GET.get('root_pk') or trek.pk
        qs = trek.trek.touristic_events.filter(published=True).prefetch_related('attachments') \
            .annotate(geom2d_transformed=Transform(F('geom'), settings.API_SRID)) \
            .order_by('pk')
        data = api_serializers_tourism.TouristicEventListSerializer(qs, many=True, context={'root_pk': root_pk}).data
        return response.Response(data)

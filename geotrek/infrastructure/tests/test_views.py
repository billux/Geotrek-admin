# -*- coding: utf-8 -*-
import datetime
import json

from django.conf import settings
from django.test import TestCase

from geotrek.common.tests import CommonTest
from geotrek.authent.tests import AuthentFixturesTest
from geotrek.authent.factories import PathManagerFactory
from geotrek.maintenance.factories import InterventionFactory
from geotrek.infrastructure.models import (Infrastructure, InfrastructureCondition, INFRASTRUCTURE_TYPES)
from geotrek.core.factories import PathFactory
from geotrek.infrastructure.factories import (InfrastructureFactory, InfrastructureNoPictogramFactory,
                                              InfrastructureTypeFactory, InfrastructureConditionFactory)
from geotrek.infrastructure.filters import InfrastructureFilterSet


class InfrastructureTest(TestCase):
    def test_helpers(self):
        p = PathFactory.create()

        infra = InfrastructureFactory.create(no_path=True)
        infra.add_path(path=p)

        self.assertItemsEqual(p.infrastructures, [infra])


class InfrastructureViewsTest(CommonTest):
    model = Infrastructure
    modelfactory = InfrastructureFactory
    userfactory = PathManagerFactory

    def get_good_data(self):
        good_data = {
            'name': 'test',
            'description': 'oh',
            'type': InfrastructureTypeFactory.create(type=INFRASTRUCTURE_TYPES.BUILDING).pk,
            'condition': InfrastructureConditionFactory.create().pk,
        }
        if settings.TREKKING_TOPOLOGY_ENABLED:
            path = PathFactory.create()
            good_data['topology'] = '{"paths": [%s]}' % path.pk
        else:
            good_data['geom'] = 'LINESTRING (0.0 0.0, 1.0 1.0)'
        return good_data

    def test_description_in_detail_page(self):
        infra = InfrastructureFactory.create(description="<b>Beautiful !</b>")
        self.login()
        response = self.client.get(infra.get_detail_url())
        self.assertContains(response, "<b>Beautiful !</b>")

    def test_check_structure_or_none_related_are_visible(self):
        self.login()
        infratype = InfrastructureTypeFactory.create(type=INFRASTRUCTURE_TYPES.BUILDING, structure=None)
        response = self.client.get(self.model.get_add_url())
        self.assertEqual(response.status_code, 200)
        self.assertTrue('form' in response.context)
        form = response.context['form']
        type = form.fields['type']
        self.assertTrue((infratype.pk, unicode(infratype)) in type.choices)

    def test_no_pictogram(self):
        self.modelfactory = InfrastructureNoPictogramFactory
        super(InfrastructureViewsTest, self).test_api_detail_for_model()


class PointInfrastructureViewsTest(InfrastructureViewsTest):
    def get_good_data(self):
        good_data = {
            'name': 'test',
            'description': 'oh',
            'type': InfrastructureTypeFactory.create(type=INFRASTRUCTURE_TYPES.BUILDING).pk,
            'condition': InfrastructureConditionFactory.create().pk,
        }
        if settings.TREKKING_TOPOLOGY_ENABLED:
            path = PathFactory.create()
            good_data['topology'] = '{"paths": [%s]}' % path.pk
        else:
            good_data['geom'] = 'POINT(0.42 0.666)'
        return good_data


class InfrastructureConditionTest(TestCase):
    def test_manager(self):
        it1 = InfrastructureConditionFactory.create()
        it2 = InfrastructureConditionFactory.create()
        it3 = InfrastructureConditionFactory.create()

        self.assertItemsEqual(InfrastructureCondition.objects.all(), [it1, it2, it3])


class InfraFilterTestMixin():
    factory = None
    filterset = None

    def login(self):
        user = PathManagerFactory(password='booh')
        success = self.client.login(username=user.username, password='booh')
        self.assertTrue(success)

    def test_intervention_filter(self):
        self.login()

        model = self.factory._meta.model
        # We will filter by this year
        year = 2014
        good_date_year = datetime.datetime(year=year, month=2, day=2)
        bad_date_year = datetime.datetime(year=year + 2, month=2, day=2)

        # Bad topology/infrastructure: No intervention
        self.factory()

        # Bad signage: intervention with wrong year
        bad_topo = self.factory()
        InterventionFactory(topology=bad_topo, date=bad_date_year)

        # Good signage: intervention with the good year
        good_topo = self.factory()
        InterventionFactory(topology=good_topo, date=good_date_year)

        data = {
            'intervention_year': year
        }
        response = self.client.get(model.get_jsonlist_url(), data)

        self.assertEqual(response.status_code, 200)
        topo_pk = json.loads(response.content)['map_obj_pk']

        self.assertItemsEqual(topo_pk, [good_topo.pk])

    def test_intervention_filter_has_correct_label(self):
        self.login()
        model = self.factory._meta.model
        response = self.client.get(model.get_list_url())
        self.assertContains(response, '<option value="-1">Intervention year</option>')

    def test_duplicate_implantation_year_filter(self):
        self.login()

        model = self.factory._meta.model
        # We will check if this
        year = 2014
        year_t = datetime.datetime(year=year, month=2, day=2)

        # Bad signage: intervention with wrong year
        topo_1 = self.factory()
        InterventionFactory(topology=topo_1, date=year_t)

        # Good signage: intervention with the good year
        topo_2 = self.factory()
        InterventionFactory(topology=topo_2, date=year_t)

        response = self.client.get(model.get_list_url())
        self.assertContains(response, '<option value="2014">2014</option>')
        response = str(response).replace('<option value="2014">2014</option>', '', 1)
        self.assertFalse('<option value="2014">2014</option>' in response)


class InfrastructureFilterTest(InfraFilterTestMixin, AuthentFixturesTest):
    factory = InfrastructureFactory
    filterset = InfrastructureFilterSet

    def test_none_implantation_year_filter(self):

        self.login()
        model = self.factory._meta.model
        InfrastructureFactory.create()
        response = self.client.get(model.get_list_url())
        self.assertFalse('option value="" selected>None</option' in str(response))

    def test_implantation_year_filter(self):
        filter = InfrastructureFilterSet(data={'implantation_year': 2015})
        self.login()
        model = self.factory._meta.model
        i = InfrastructureFactory.create(implantation_year=2015)
        i2 = InfrastructureFactory.create(implantation_year=2016)
        response = self.client.get(model.get_list_url())

        self.assertTrue('<option value="2015">2015</option>' in str(response))
        self.assertTrue('<option value="2016">2016</option>' in str(response))

        self.assertTrue(i in filter.qs)
        self.assertFalse(i2 in filter.qs)

    def test_implantation_year_filter_with_str(self):
        filter = InfrastructureFilterSet(data={'implantation_year': 'toto'})
        self.login()
        model = self.factory._meta.model
        i = InfrastructureFactory.create(implantation_year=2015)
        i2 = InfrastructureFactory.create(implantation_year=2016)
        response = self.client.get(model.get_list_url())

        self.assertTrue('<option value="2015">2015</option>' in str(response))
        self.assertTrue('<option value="2016">2016</option>' in str(response))

        self.assertIn(i, filter.qs)
        self.assertIn(i2, filter.qs)

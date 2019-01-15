import os

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.gis.db import models as gismodels
from django.conf import settings

from mapentity.models import MapEntityMixin

from geotrek.core.models import Topology, Path
from geotrek.authent.models import StructureOrNoneRelated, StructureRelated
from geotrek.common.mixins import OptionalPictogramMixin
from geotrek.common.models import Organism
from geotrek.infrastructure.models import BaseInfrastructure, InfrastructureCondition


class Sealing(StructureOrNoneRelated):
    """ A sealing linked with a signage"""
    label = models.CharField(verbose_name=_(u"Name"), db_column="etat", max_length=250)

    class Meta:
        db_table = 's_b_scellement'
        verbose_name = _(u"Sealing")
        verbose_name_plural = _(u"Sealings")

    def __unicode__(self):
        if self.structure:
            return u"{} ({})".format(self.label, self.structure.name)
        return self.label


class SignageType(StructureOrNoneRelated, OptionalPictogramMixin):
    """ Types of infrastructures (bridge, WC, stairs, ...) """
    label = models.CharField(db_column="nom", max_length=128)

    class Meta:
        db_table = 's_b_signaletique'
        verbose_name = _(u"Signage Type")
        verbose_name_plural = _(u"Signage Types")

    def __unicode__(self):
        if self.structure:
            return u"{} ({})".format(self.label, self.structure.name)
        return self.label

    def get_pictogram_url(self):
        pictogram_url = super(SignageType, self).get_pictogram_url()
        if pictogram_url:
            return pictogram_url
        return os.path.join(settings.STATIC_URL, 'infrastructure/picto-signage.png')


class SignageGISManager(gismodels.GeoManager):
    """ Overide default typology mixin manager, and filter by type. """
    def all_implantation_years(self):
        all_years = self.get_queryset().filter(implantation_year__isnull=False)\
            .order_by('-implantation_year').values_list('implantation_year', flat=True).distinct('implantation_year')
        return all_years


class Signage(MapEntityMixin, BaseInfrastructure):
    """ An infrastructure in the park, which is of type SIGNAGE """
    objects = BaseInfrastructure.get_manager_cls(SignageGISManager)()
    code = models.CharField(verbose_name=_(u"Code"), max_length=250, blank=True, null=True,
                            db_column='code')
    manager = models.ForeignKey(Organism, db_column='gestionnaire', verbose_name=_("Manager"), null=True, blank=True)
    sealing = models.ForeignKey(Sealing, db_column='scellement', verbose_name=_("Sealing"), null=True, blank=True)
    printed_elevation = models.IntegerField(verbose_name=_(u"Printed Elevation"), blank=True, null=True,
                                            db_column='altitude_imprimee')
    type = models.ForeignKey(SignageType, db_column='type', verbose_name=_("Type"))

    class Meta:
        db_table = 's_t_signaletique'
        verbose_name = _(u"Signage")
        verbose_name_plural = _(u"Signages")

    @classmethod
    def path_signages(cls, path):
        return cls.objects.existing().filter(aggregations__path=path).distinct('pk')

    @classmethod
    def topology_signages(cls, topology):
        return cls.overlapping(topology)

    @classmethod
    def published_topology_signages(cls, topology):
        return cls.topology_signages(topology).filter(published=True)


Path.add_property('signages', lambda self: Signage.path_signages(self), _(u"Signages"))
Topology.add_property('signages', lambda self: Signage.topology_signages(self), _(u"Signages"))
Topology.add_property('published_signages', lambda self: Signage.published_topology_signages(self),
                      _(u"Published Signages"))


class Orientation(models.Model):
    label = models.CharField(db_column="etiquette", max_length=128)

    class Meta:
        db_table = 's_b_orientation'
        verbose_name = _(u"Orientation")
        verbose_name_plural = _(u"Orientations")


class Color(models.Model):
    label = models.CharField(db_column="etiquette", max_length=128)

    class Meta:
        db_table = 's_b_color'
        verbose_name = _(u"Color Blade")
        verbose_name_plural = _(u"Colors Blade")


class Blade(StructureRelated):
    signage = models.ForeignKey(Signage, db_column='signaletique', verbose_name=_("Signage"),
                                on_delete=models.PROTECT)
    number = models.IntegerField(verbose_name=_(u"Blade Number"), db_column='numero')
    orientation = models.ForeignKey(Orientation, verbose_name=_(u"Orientation"), db_column='orientation',
                                    on_delete=models.PROTECT)
    type = models.CharField(verbose_name=_(u"Blade Type"), max_length=250, db_column='type')
    color = models.ForeignKey(Color, db_column='couleur', on_delete=models.PROTECT, null=True, blank=True)
    condition = models.ForeignKey(InfrastructureCondition, db_column='etat', verbose_name=_("Condition"),
                                  null=True, blank=True, on_delete=models.PROTECT)

    class Meta:
        db_table = 's_t_lame'
        verbose_name = _(u"Blade")
        verbose_name_plural = _(u"Blades")


class Line(StructureRelated):
    blade = models.ForeignKey(Blade, db_column='lame', verbose_name=_("Blade"), on_delete=models.PROTECT)
    number = models.IntegerField(db_column='nombre', verbose_name=_("Number"))
    text = models.CharField(db_column='texte', verbose_name=_("Text"), max_length=1000)
    distance = models.DecimalField(db_column='distance', verbose_name=_("Distance"), null=True, blank=True,
                                   decimal_places=3, max_digits=8)
    pictogram_name = models.CharField(db_column='nom_pictogramme', verbose_name=_("Name pictogramm"), max_length=250,
                                      blank=True, null=True)
    time = models.DurationField(db_column='temps', verbose_name=_("Temps"), null=True, blank=True)

    class Meta:
        db_table = 's_t_ligne'
        verbose_name = _(u"Line")
        verbose_name_plural = _(u"Lines")
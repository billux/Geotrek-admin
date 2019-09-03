import logging
import re

from django.db import connection
from django.utils.timezone import utc
from django.conf import settings
from django.contrib.gis.measure import Distance

from mapentity.serializers import plain_text


logger = logging.getLogger(__name__)


class classproperty(object):
    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter(owner)


# This one come from pyramid
# https://github.com/Pylons/pyramid/blob/master/pyramid/decorator.py
class reify(object):

    """ Put the result of a method which uses this (non-data)
    descriptor decorator in the instance dict after the first call,
    effectively replacing the decorator with an instance variable."""

    def __init__(self, wrapped):
        self.wrapped = wrapped
        try:
            self.__doc__ = wrapped.__doc__
        except AttributeError:
            pass

    def __get__(self, inst, objtype=None):
        if inst is None:
            return self
        val = self.wrapped(inst)
        setattr(inst, self.wrapped.__name__, val)
        return val


def dbnow():
    cursor = connection.cursor()
    cursor.execute("SELECT statement_timestamp() AT TIME ZONE 'UTC';")
    row = cursor.fetchone()
    return row[0].replace(tzinfo=utc)


def sql_extent(sql):
    """ Given a SQL query that returns a BOX(), returns
    tuple (xmin, ymin, xmax, ymax)
    """
    cursor = connection.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    row = result[0]
    extent = row[0] or '0 0 0 0'
    value = extent.replace('BOX(', '').replace(')', '').replace(',', ' ')
    return tuple([float(v) for v in value.split()])


def sqlfunction(function, *args):
    """
    Executes the SQL function with the specified args, and returns the result.
    """
    sql = '%s(%s)' % (function, ','.join(args))
    logger.debug(sql)
    cursor = connection.cursor()
    cursor.execute(sql)
    result = cursor.fetchall()
    if len(result) == 1:
        return result[0]
    return result


def uniquify(values):
    """
    Return unique values, order preserved
    """
    unique = []
    [unique.append(i) for i in values if i not in unique]
    return unique


def intersecting(cls, obj, distance=None):
    """
    Small helper to filter all model instances by geometry intersection
    """
    qs = cls.objects
    if not obj.geom:
        return qs.none()
    if hasattr(qs, 'existing'):
        qs = qs.existing()
    if distance is None:
        distance = obj.distance(cls)
    if distance:
        qs = qs.filter(geom__dwithin=(obj.geom, Distance(m=distance)))
    else:
        qs = qs.filter(geom__intersects=obj.geom)
        if obj.geom.geom_type == 'LineString':
            # FIXME: move transform from DRF viewset to DRF itself and remove transform here
            ewkt = obj.geom.transform(settings.SRID, clone=True).ewkt
            qs = qs.extra(select={'ordering': 'ST_LineLocatePoint(ST_GeomFromEWKT(\'{ewkt}\'), ST_StartPoint((ST_Dump(ST_Intersection(ST_GeomFromEWKT(\'{ewkt}\'), geom))).geom))'.format(ewkt=ewkt)})
            qs = qs.extra(order_by=['ordering'])

    if obj.__class__ == cls:
        # Prevent self intersection
        qs = qs.exclude(pk=obj.pk)
    return qs

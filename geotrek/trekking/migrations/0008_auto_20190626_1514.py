# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2019-06-26 13:14
from __future__ import unicode_literals

import colorfield.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trekking', '0007_auto_20190626_1514'),
    ]

    operations = [
        migrations.AlterField(
            model_name='practice',
            name='color',
            field=colorfield.fields.ColorField(db_column=b'couleur', default=b'#444444', max_length=18, verbose_name='Color (mobile app only)'),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-12-08 22:41
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ratatouille', '0006_auto_20161110_2245'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='menuitems',
            name='mia',
        ),
        migrations.RemoveField(
            model_name='menuitems',
            name='mib',
        ),
        migrations.RemoveField(
            model_name='menuitems',
            name='mic',
        ),
    ]
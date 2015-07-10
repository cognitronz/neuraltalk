# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('task_id', models.CharField(max_length=35)),
                ('task_type', models.CharField(max_length=30)),
                ('data_input', models.TextField()),
                ('data_output', models.TextField()),
                ('status', models.CharField(max_length=15)),
            ],
        ),
    ]

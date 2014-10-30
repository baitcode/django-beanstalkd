# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Job',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, auto_created=True)),
                ('beanstalk_id', models.IntegerField()),
                ('instance_ip', models.IPAddressField()),
                ('instance_port', models.IntegerField()),
                ('tube_name', models.CharField(max_length=1000)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('digest', models.CharField(max_length=32, null=True)),
                ('message', django_extensions.db.fields.json.JSONField()),
                ('state', models.SmallIntegerField(default=1, choices=[(1, b'in queue'), (2, b'buried'), (3, b'complete'), (4, b'processing'), (5, b'delayed'), (6, b'failed')])),
            ],
            options={
                'db_table': 'beanstalk_job',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Tube',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=1000)),
                ('buried', models.IntegerField(null=True)),
                ('delayed', models.IntegerField(null=True)),
                ('ready', models.IntegerField(null=True)),
                ('reserved', models.IntegerField(null=True)),
                ('urgent', models.IntegerField(null=True)),
            ],
            options={
                'ordering': ['name'],
                'db_table': 'beanstalk_tube',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='job',
            name='tube',
            field=models.ForeignKey(to='beanstalkd.Tube', null=True),
            preserve_default=True,
        ),
        migrations.AlterIndexTogether(
            name='job',
            index_together=set([('digest',)]),
        ),
    ]

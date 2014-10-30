# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Tube'
        db.create_table('beanstalk_tube', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('buried', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('delayed', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('ready', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('reserved', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('urgent', self.gf('django.db.models.fields.IntegerField')(null=True)),
        ))
        db.send_create_signal('beanstalkd', ['Tube'])

        # Adding model 'Job'
        db.create_table('beanstalk_job', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('beanstalk_id', self.gf('django.db.models.fields.IntegerField')()),
            ('instance_ip', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
            ('instance_port', self.gf('django.db.models.fields.IntegerField')()),
            ('tube', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['beanstalk.Tube'], null=True)),
            ('tube_name', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('message', self.gf('django.db.models.fields.TextField')(default='{}')),
            ('state', self.gf('django.db.models.fields.SmallIntegerField')(default=1)),
        ))
        db.send_create_signal('beanstalkd', ['Job'])

    def backwards(self, orm):
        
        # Deleting model 'Tube'
        db.delete_table('beanstalk_tube')

        # Deleting model 'Job'
        db.delete_table('beanstalk_job')


    models = {
        'beanstalk.job': {
            'Meta': {'object_name': 'Job'},
            'beanstalk_id': ('django.db.models.fields.IntegerField', [], {}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance_ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'instance_port': ('django.db.models.fields.IntegerField', [], {}),
            'message': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'state': ('django.db.models.fields.SmallIntegerField', [], {'default': '1'}),
            'tube': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['beanstalk.Tube']", 'null': 'True'}),
            'tube_name': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'beanstalk.tube': {
            'Meta': {'ordering': "['name']", 'object_name': 'Tube'},
            'buried': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'delayed': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'ready': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'reserved': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'urgent': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        }
    }

    complete_apps = ['beanstalkd']

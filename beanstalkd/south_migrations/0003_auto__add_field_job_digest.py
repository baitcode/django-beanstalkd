# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Job.digest'
        db.add_column(u'beanstalk_job', 'digest', self.gf('django.db.models.fields.CharField')(max_length=32, null=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Job.digest'
        db.delete_column(u'beanstalk_job', 'digest')


    models = {
        u'beanstalkd.job': {
            'Meta': {'object_name': 'Job'},
            'beanstalk_id': ('django.db.models.fields.IntegerField', [], {}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'digest': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance_ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'instance_port': ('django.db.models.fields.IntegerField', [], {}),
            'message': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'state': ('django.db.models.fields.SmallIntegerField', [], {'default': '1'}),
            'tube': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['beanstalkd.Tube']", 'null': 'True'}),
            'tube_name': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'beanstalkd.tube': {
            'Meta': {'ordering': "['name']", 'object_name': 'Tube'},
            'buried': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'delayed': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'ready': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'reserved': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'urgent': ('django.db.models.fields.IntegerField', [], {'null': 'True'})
        }
    }

    complete_apps = ['beanstalkd']

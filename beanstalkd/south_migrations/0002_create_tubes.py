# encoding: utf-8
from south.v2 import DataMigration
from beanstalkd import tubes


class Migration(DataMigration):

    def forwards(self, orm):
        for tube in tubes.as_list():
            orm['beanstalkd.Tube'].objects.create(
                name=tube
            )
        tubes.reset_registry()

    def backwards(self, orm):
        "Write your backwards methods here."


    models = {
        'beanstalkd.job': {
            'Meta': {'object_name': 'Job'},
            'beanstalk_id': ('django.db.models.fields.IntegerField', [], {}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance_ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'instance_port': ('django.db.models.fields.IntegerField', [], {}),
            'message': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'state': ('django.db.models.fields.SmallIntegerField', [], {'default': '1'}),
            'tube': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['beanstalkd.Tube']", 'null': 'True'}),
            'tube_name': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'beanstalkd.tube': {
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

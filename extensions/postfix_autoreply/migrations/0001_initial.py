# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Transport'
        db.create_table('postfix_autoreply_transport', (
            ('domain', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('method', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('postfix_autoreply', ['Transport'])

        # Adding model 'Alias'
        db.create_table('postfix_autoreply_alias', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('full_address', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('autoreply_address', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('postfix_autoreply', ['Alias'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Transport'
        db.delete_table('postfix_autoreply_transport')

        # Deleting model 'Alias'
        db.delete_table('postfix_autoreply_alias')
    
    
    models = {
        'postfix_autoreply.alias': {
            'Meta': {'object_name': 'Alias'},
            'autoreply_address': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'full_address': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'postfix_autoreply.transport': {
            'Meta': {'object_name': 'Transport'},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }
    
    complete_apps = ['postfix_autoreply']

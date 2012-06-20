# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from modoboa.lib.dbutils import db_table_exists

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        # Renaming/Creating model 'ARmessage'
        if db_table_exists('main_armessage'):
            db.rename_table('main_armessage', 'postfix_autoreply_armessage')
        else:
            db.create_table('postfix_autoreply_armessage', (
                    ('mbox', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['admin.Mailbox'])),
                    ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                    ('subject', self.gf('django.db.models.fields.CharField')(max_length=255)),
                    ('content', self.gf('django.db.models.fields.TextField')()),
                    ('enabled', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True))
                    ))
            db.send_create_signal('postfix_autoreply', ['ARmessage'])

        db.add_column('postfix_autoreply_armessage', 'untildate',
                      models.DateTimeField(null=True))

        # Renaming model 'ARhistoric'
        if db_table_exists('main_arhistoric'):
            db.rename_table('main_arhistoric', 'postfix_autoreply_arhistoric')
        else:
            db.create_table('postfix_autoreply_arhistoric', (
                    ('armessage', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['postfix_autoreply.ARmessage'])),
                    ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
                    ('last_sent', self.gf('django.db.models.fields.DateTimeField')(auto_now=True)),
                    ('sender', self.gf('django.db.models.fields.TextField')()),
                    ))
            db.send_create_signal('postfix_autoreply', ['ARhistoric'])
    
    
    def backwards(self, orm):
        raise RuntimeError("Cannot reverse this migration.")
    
    
    models = {
        'admin.domain': {
            'Meta': {'object_name': 'Domain'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'quota': ('django.db.models.fields.IntegerField', [], {})
        },
        'admin.mailbox': {
            'Meta': {'object_name': 'Mailbox'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'domain': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['admin.Domain']"}),
            'full_address': ('django.db.models.fields.CharField', [], {'max_length': '150'}),
            'gid': ('django.db.models.fields.IntegerField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'quota': ('django.db.models.fields.IntegerField', [], {}),
            'uid': ('django.db.models.fields.IntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'postfix_autoreply.alias': {
            'Meta': {'object_name': 'Alias'},
            'autoreply_address': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'full_address': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'postfix_autoreply.arhistoric': {
            'Meta': {'object_name': 'ARhistoric'},
            'armessage': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['postfix_autoreply.ARmessage']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_sent': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'sender': ('django.db.models.fields.TextField', [], {})
        },
        'postfix_autoreply.armessage': {
            'Meta': {'object_name': 'ARmessage'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mbox': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['admin.Mailbox']"}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'untildate': ('django.db.models.fields.DateTimeField', [], {})
        },
        'postfix_autoreply.transport': {
            'Meta': {'object_name': 'Transport'},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }
    
    complete_apps = ['postfix_autoreply']

# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        for mailbox in orm.Mailbox.objects.all():
            quota, created = orm.Quota.objects.get_or_create(
                pk="%s@%s" % (mailbox.address, mailbox.domain.name)
            )
            mailbox.quota_value = quota
            mailbox.save()

    def backwards(self, orm):
        "Write your backwards methods here."
        for mailbox in orm.Mailbox.objects.all():
            mailbox.quota_value = None
            mailbox.save()

    models = {
        'admin.alias': {
            'Meta': {'ordering': "['domain__name', 'address']", 'unique_together': "(('address', 'domain'),)", 'object_name': 'Alias'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '254'}),
            'aliases': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['admin.Alias']", 'symmetrical': 'False'}),
            'dates': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['admin.ObjectDates']"}),
            'domain': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['admin.Domain']"}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'extmboxes': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mboxes': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['admin.Mailbox']", 'symmetrical': 'False'})
        },
        'admin.domain': {
            'Meta': {'ordering': "['name']", 'object_name': 'Domain'},
            'dates': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['admin.ObjectDates']"}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'quota': ('django.db.models.fields.IntegerField', [], {})
        },
        'admin.domainalias': {
            'Meta': {'object_name': 'DomainAlias'},
            'dates': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['admin.ObjectDates']"}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['admin.Domain']"})
        },
        'admin.mailbox': {
            'Meta': {'object_name': 'Mailbox'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '252'}),
            'dates': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['admin.ObjectDates']"}),
            'domain': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['admin.Domain']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'quota': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'quota_value': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['admin.Quota']", 'null': 'True'}),
            'use_domain_quota': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.User']"})
        },
        'admin.mailboxoperation': {
            'Meta': {'object_name': 'MailboxOperation'},
            'argument': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mailbox': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['admin.Mailbox']", 'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        },
        'admin.objectdates': {
            'Meta': {'object_name': 'ObjectDates'},
            'creation': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_modification': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'admin.quota': {
            'Meta': {'object_name': 'Quota'},
            'bytes': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'messages': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'username': ('django.db.models.fields.EmailField', [], {'max_length': '254', 'primary_key': 'True'})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'core.objectaccess': {
            'Meta': {'unique_together': "(('user', 'content_type', 'object_id'),)", 'object_name': 'ObjectAccess'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_owner': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['core.User']"})
        },
        u'core.user': {
            'Meta': {'ordering': "['username']", 'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '254', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_local': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '254'})
        }
    }

    complete_apps = ['admin']
    symmetrical = True

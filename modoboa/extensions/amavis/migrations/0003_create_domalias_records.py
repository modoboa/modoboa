# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        try:
            ext = orm["core.Extension"].objects.get(name="amavis")
        except ObjectDoesNotExist:
            return
        if not ext.enabled:
            return
        for domalias in orm["admin.DomainAlias"].objects.all():
            u = orm["amavis.Users"](
                email="@%s" % domalias.name, fullname=domalias.name, priority=7
            )
            u.policy = orm["amavis.Policy"].objects.get(policy_name=domalias.target.name)
            u.save()

    def backwards(self, orm):
        "Write your backwards methods here."
        raise RuntimeError("Cannot revert this migration")

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
            'mbox': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'quota_value'", 'unique': 'True', 'null': 'True', 'to': "orm['admin.Mailbox']"}),
            'messages': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'username': ('django.db.models.fields.EmailField', [], {'max_length': '254', 'primary_key': 'True'})
        },
        u'amavis.maddr': {
            'Meta': {'object_name': 'Maddr', 'db_table': "u'maddr'", 'managed': 'False'},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '765'}),
            'email': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'partition_tag': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'amavis.mailaddr': {
            'Meta': {'object_name': 'Mailaddr', 'db_table': "u'mailaddr'", 'managed': 'False'},
            'email': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {})
        },
        u'amavis.msgrcpt': {
            'Meta': {'unique_together': "(('partition_tag', 'mail', 'rseqnum'),)", 'object_name': 'Msgrcpt', 'db_table': "u'msgrcpt'", 'managed': 'False'},
            'bl': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'bspam_level': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'content': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'ds': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'is_local': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'mail': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['amavis.Msgs']", 'primary_key': 'True'}),
            'partition_tag': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rid': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['amavis.Maddr']", 'primary_key': 'True', 'db_column': "'rid'"}),
            'rs': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'rseqnum': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'smtp_resp': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'wl': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'})
        },
        u'amavis.msgs': {
            'Meta': {'unique_together': "(('partition_tag', 'mail_id'),)", 'object_name': 'Msgs', 'db_table': "u'msgs'", 'managed': 'False'},
            'am_id': ('django.db.models.fields.CharField', [], {'max_length': '60'}),
            'client_addr': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'content': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'dsn_sent': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'from_addr': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'host': ('django.db.models.fields.CharField', [], {'max_length': '765'}),
            'mail_id': ('django.db.models.fields.CharField', [], {'max_length': '12', 'primary_key': 'True'}),
            'message_id': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'originating': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'partition_tag': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'policy': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'quar_loc': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'quar_type': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'secret_id': ('django.db.models.fields.CharField', [], {'max_length': '12', 'blank': 'True'}),
            'sid': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['amavis.Maddr']", 'db_column': "'sid'"}),
            'size': ('django.db.models.fields.IntegerField', [], {}),
            'spam_level': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'time_iso': ('django.db.models.fields.CharField', [], {'max_length': '48'}),
            'time_num': ('django.db.models.fields.IntegerField', [], {})
        },
        u'amavis.policy': {
            'Meta': {'object_name': 'Policy', 'db_table': "u'policy'", 'managed': 'False'},
            'addr_extension_bad_header': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'addr_extension_banned': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'addr_extension_spam': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'addr_extension_virus': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'archive_quarantine_to': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'bad_header_admin': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'bad_header_lover': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'bad_header_quarantine_to': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'banned_admin': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'banned_files_lover': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'banned_quarantine_to': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'banned_rulenames': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'bypass_banned_checks': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '3', 'null': 'True'}),
            'bypass_header_checks': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'bypass_spam_checks': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '3', 'null': 'True'}),
            'bypass_virus_checks': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '3', 'null': 'True'}),
            'clean_quarantine_to': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'disclaimer_options': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'forward_method': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message_size_limit': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'newvirus_admin': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'policy_name': ('django.db.models.fields.CharField', [], {'max_length': '96', 'blank': 'True'}),
            'sa_userconf': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'sa_username': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'spam_admin': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'spam_dsn_cutoff_level': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'spam_kill_level': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'spam_lover': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'spam_quarantine_cutoff_level': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'spam_quarantine_to': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'spam_subject_tag': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'spam_subject_tag2': ('django.db.models.fields.CharField', [], {'default': 'None', 'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'spam_subject_tag3': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'spam_tag2_level': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'spam_tag3_level': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'spam_tag_level': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'unchecked_lover': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'unchecked_quarantine_to': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'virus_admin': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'virus_lover': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'virus_quarantine_to': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
            'warnbadhrecip': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'warnbannedrecip': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'}),
            'warnvirusrecip': ('django.db.models.fields.CharField', [], {'max_length': '3', 'null': 'True', 'blank': 'True'})
        },
        u'amavis.quarantine': {
            'Meta': {'ordering': "['-mail__time_num']", 'unique_together': "(('partition_tag', 'mail', 'chunk_ind'),)", 'object_name': 'Quarantine', 'db_table': "u'quarantine'", 'managed': 'False'},
            'chunk_ind': ('django.db.models.fields.IntegerField', [], {}),
            'mail': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['amavis.Msgs']", 'primary_key': 'True'}),
            'mail_text': ('django.db.models.fields.TextField', [], {}),
            'partition_tag': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'amavis.users': {
            'Meta': {'object_name': 'Users', 'db_table': "u'users'", 'managed': 'False'},
            'email': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'fullname': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'policy': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['amavis.Policy']"}),
            'priority': ('django.db.models.fields.IntegerField', [], {})
        },
        u'amavis.wblist': {
            'Meta': {'object_name': 'Wblist', 'db_table': "u'wblist'", 'managed': 'False'},
            'rid': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'sid': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'wb': ('django.db.models.fields.CharField', [], {'max_length': '30'})
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
        u'core.extension': {
            'Meta': {'object_name': 'Extension'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150'})
        },
        u'core.log': {
            'Meta': {'object_name': 'Log'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'logger': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'message': ('django.db.models.fields.CharField', [], {'max_length': '255'})
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
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '254'})
        }
    }

    complete_apps = ['core', 'admin', 'amavis']
    symmetrical = True

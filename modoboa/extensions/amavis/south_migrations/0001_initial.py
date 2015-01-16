# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        pass

    def backwards(self, orm):
        pass

    models = {
        'amavis.maddr': {
            'Meta': {'object_name': 'Maddr', 'db_table': "u'maddr'", 'managed': 'False'},
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '765'}),
            'email': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.BigIntegerField', [], {'primary_key': 'True'}),
            'partition_tag': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True', 'blank': 'True'})
        },
        'amavis.mailaddr': {
            'Meta': {'object_name': 'Mailaddr', 'db_table': "u'mailaddr'", 'managed': 'False'},
            'email': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'priority': ('django.db.models.fields.IntegerField', [], {})
        },
        'amavis.msgrcpt': {
            'Meta': {'unique_together': "(('partition_tag', 'mail', 'rseqnum'),)", 'object_name': 'Msgrcpt', 'db_table': "u'msgrcpt'", 'managed': 'False'},
            'bl': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'}),
            'bspam_level': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'content': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'ds': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'is_local': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'mail': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['amavis.Msgs']", 'primary_key': 'True'}),
            'partition_tag': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'rid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['amavis.Maddr']", 'primary_key': 'True', 'db_column': "'rid'"}),
            'rs': ('django.db.models.fields.CharField', [], {'max_length': '3'}),
            'rseqnum': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'smtp_resp': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'wl': ('django.db.models.fields.CharField', [], {'max_length': '3', 'blank': 'True'})
        },
        'amavis.msgs': {
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
            'sid': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['amavis.Maddr']", 'db_column': "'sid'"}),
            'size': ('django.db.models.fields.IntegerField', [], {}),
            'spam_level': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'subject': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'time_iso': ('django.db.models.fields.CharField', [], {'max_length': '48'}),
            'time_num': ('django.db.models.fields.IntegerField', [], {})
        },
        'amavis.policy': {
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
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            'spam_subject_tag2': ('django.db.models.fields.CharField', [], {'max_length': '192', 'null': 'True', 'blank': 'True'}),
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
        'amavis.quarantine': {
            'Meta': {'ordering': "['-mail__time_num']", 'unique_together': "(('partition_tag', 'mail', 'chunk_ind'),)", 'object_name': 'Quarantine', 'db_table': "u'quarantine'", 'managed': 'False'},
            'chunk_ind': ('django.db.models.fields.IntegerField', [], {}),
            'mail': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['amavis.Msgs']", 'primary_key': 'True'}),
            'mail_text': ('django.db.models.fields.TextField', [], {}),
            'partition_tag': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'amavis.users': {
            'Meta': {'object_name': 'Users', 'db_table': "u'users'", 'managed': 'False'},
            'email': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'fullname': ('django.db.models.fields.CharField', [], {'max_length': '765', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'policy': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['amavis.Policy']"}),
            'priority': ('django.db.models.fields.IntegerField', [], {})
        },
        'amavis.wblist': {
            'Meta': {'object_name': 'Wblist', 'db_table': "u'wblist'", 'managed': 'False'},
            'rid': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'sid': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True'}),
            'wb': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        }
    }

    complete_apps = ['amavis']

# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.
#
# Original Amavis version : 2.6.2

from django.db import models
from django.utils.translation import ugettext_lazy


class Maddr(models.Model):
    partition_tag = models.IntegerField(unique=True, null=True, blank=True)
    id = models.BigIntegerField(primary_key=True)
    email = models.CharField(unique=True, max_length=255)
    domain = models.CharField(max_length=765)

    class Meta:
        db_table = u'maddr'
        managed = False


class Mailaddr(models.Model):
    id = models.IntegerField(primary_key=True)
    priority = models.IntegerField()
    email = models.CharField(unique=True, max_length=255)

    class Meta:
        db_table = u'mailaddr'
        managed = False


class Msgs(models.Model):
    partition_tag = models.IntegerField(null=True, blank=True)
    mail_id = models.CharField(max_length=12, primary_key=True)
    secret_id = models.CharField(max_length=12, blank=True)
    am_id = models.CharField(max_length=60)
    time_num = models.IntegerField()
    time_iso = models.CharField(max_length=48)
    sid = models.ForeignKey(Maddr, db_column='sid')
    policy = models.CharField(max_length=765, blank=True)
    client_addr = models.CharField(max_length=765, blank=True)
    size = models.IntegerField()
    originating = models.CharField(max_length=3)
    content = models.CharField(max_length=1, blank=True)
    quar_type = models.CharField(max_length=1, blank=True)
    quar_loc = models.CharField(max_length=255, blank=True)
    dsn_sent = models.CharField(max_length=3, blank=True)
    spam_level = models.FloatField(null=True, blank=True)
    message_id = models.CharField(max_length=765, blank=True)
    from_addr = models.CharField(max_length=765, blank=True)
    subject = models.CharField(max_length=765, blank=True)
    host = models.CharField(max_length=765)

    class Meta:
        db_table = u'msgs'
        managed = False
        unique_together = ('partition_tag', 'mail_id')


class Msgrcpt(models.Model):
    partition_tag = models.IntegerField(null=True, blank=True)
    mail = models.ForeignKey(Msgs, primary_key=True)
    rid = models.ForeignKey(Maddr, db_column='rid')
    rseqnum = models.IntegerField(default=0)
    is_local = models.CharField(max_length=3)
    content = models.CharField(max_length=3)
    ds = models.CharField(max_length=3)
    rs = models.CharField(max_length=3)
    bl = models.CharField(max_length=3, blank=True)
    wl = models.CharField(max_length=3, blank=True)
    bspam_level = models.FloatField(null=True, blank=True)
    smtp_resp = models.CharField(max_length=765, blank=True)

    class Meta:
        db_table = u'msgrcpt'
        managed = False
        unique_together = ("partition_tag", "mail", "rseqnum")


class Policy(models.Model):
    policy_name = models.CharField(max_length=32, blank=True)
    virus_lover = models.CharField(max_length=3, blank=True, null=True)
    spam_lover = models.CharField(max_length=3, blank=True, null=True)
    unchecked_lover = models.CharField(max_length=3, blank=True, null=True)
    banned_files_lover = models.CharField(max_length=3, blank=True, null=True)
    bad_header_lover = models.CharField(max_length=3, blank=True, null=True)
    bypass_virus_checks = models.CharField(
        ugettext_lazy("Virus filter"), default='', null=True,
        choices=(('N', ugettext_lazy('yes')),
                 ('Y', ugettext_lazy('no')),
                 ('', ugettext_lazy('default'))),
        max_length=3,
        help_text=ugettext_lazy("Bypass virus checks or not. Choose 'default' to use global settings.")
        )
    bypass_spam_checks = models.CharField(
        ugettext_lazy("Spam filter"), default='', null=True,
        choices=(('N', ugettext_lazy('yes')),
                 ('Y', ugettext_lazy('no')),
                 ('', ugettext_lazy('default'))),
        max_length=3,
        help_text=ugettext_lazy("Bypass spam checks or not. Choose 'default' to use global settings.")
        )
    bypass_banned_checks = models.CharField(
        ugettext_lazy("Banned filter"), default='', null=True,
        choices=(('N', ugettext_lazy('yes')),
                 ('Y', ugettext_lazy('no')),
                 ('', ugettext_lazy('default'))),
        max_length=3,
        help_text=ugettext_lazy("Bypass banned checks or not. Choose 'default' to use global settings.")
        )
    bypass_header_checks = models.CharField(max_length=3, blank=True, null=True)
    virus_quarantine_to = models.CharField(max_length=192, blank=True, null=True)
    spam_quarantine_to = models.CharField(max_length=192, blank=True, null=True)
    banned_quarantine_to = models.CharField(max_length=192, blank=True, null=True)
    unchecked_quarantine_to = models.CharField(max_length=192, blank=True, null=True)
    bad_header_quarantine_to = models.CharField(max_length=192, blank=True, null=True)
    clean_quarantine_to = models.CharField(max_length=192, blank=True, null=True)
    archive_quarantine_to = models.CharField(max_length=192, blank=True, null=True)
    spam_tag_level = models.FloatField(null=True, blank=True)
    spam_tag2_level = models.FloatField(null=True, blank=True)
    spam_tag3_level = models.FloatField(null=True, blank=True)
    spam_kill_level = models.FloatField(null=True, blank=True)
    spam_dsn_cutoff_level = models.FloatField(null=True, blank=True)
    spam_quarantine_cutoff_level = models.FloatField(null=True, blank=True)
    addr_extension_virus = models.CharField(max_length=192, blank=True, null=True)
    addr_extension_spam = models.CharField(max_length=192, blank=True, null=True)
    addr_extension_banned = models.CharField(max_length=192, blank=True, null=True)
    addr_extension_bad_header = models.CharField(max_length=192, blank=True, null=True)
    warnvirusrecip = models.CharField(max_length=3, blank=True, null=True)
    warnbannedrecip = models.CharField(max_length=3, blank=True, null=True)
    warnbadhrecip = models.CharField(max_length=3, blank=True, null=True)
    newvirus_admin = models.CharField(max_length=192, blank=True, null=True)
    virus_admin = models.CharField(max_length=192, blank=True, null=True)
    banned_admin = models.CharField(max_length=192, blank=True, null=True)
    bad_header_admin = models.CharField(max_length=192, blank=True, null=True)
    spam_admin = models.CharField(max_length=192, blank=True, null=True)
    spam_subject_tag = models.CharField(max_length=192, blank=True, null=True)
    spam_subject_tag2 = models.CharField(
        ugettext_lazy("Spam marker"), default=None,
        max_length=192, blank=True, null=True,
        help_text=ugettext_lazy("Modify spam subject using the specified text. Choose 'default' to use global settings.")
        )
    spam_subject_tag3 = models.CharField(max_length=192, blank=True, null=True)
    message_size_limit = models.IntegerField(null=True, blank=True)
    banned_rulenames = models.CharField(max_length=192, blank=True, null=True)
    disclaimer_options = models.CharField(max_length=192, blank=True, null=True)
    forward_method = models.CharField(max_length=192, blank=True, null=True)
    sa_userconf = models.CharField(max_length=192, blank=True, null=True)
    sa_username = models.CharField(max_length=192, blank=True, null=True)

    class Meta:
        db_table = u'policy'
        managed = False


class Quarantine(models.Model):
    partition_tag = models.IntegerField(null=True, blank=True)
    mail = models.ForeignKey(Msgs, primary_key=True)
    chunk_ind = models.IntegerField()
    mail_text = models.BinaryField()

    class Meta:
        db_table = u'quarantine'
        managed = False
        ordering = ["-mail__time_num"]
        unique_together = ("partition_tag", "mail", "chunk_ind")


class Users(models.Model):
    id = models.AutoField(primary_key=True)
    priority = models.IntegerField()
    policy = models.ForeignKey(Policy)
    email = models.CharField(unique=True, max_length=255)
    fullname = models.CharField(max_length=765, blank=True)

    class Meta:
        db_table = u'users'
        managed = False


class Wblist(models.Model):
    rid = models.IntegerField(primary_key=True)
    sid = models.IntegerField(primary_key=True)
    wb = models.CharField(max_length=30)

    class Meta:
        db_table = u'wblist'
        managed = False

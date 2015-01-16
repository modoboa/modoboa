# coding: utf-8

"""postfixadmin models."""

# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or
# field names.
#
# Also note: You'll have to insert the output of 'django-admin.py
# sqlcustom [appname]' into your database.

from django.db import models


class Admin(models.Model):
    username = models.CharField(max_length=255, primary_key=True)
    password = models.CharField(max_length=255)
    created = models.DateTimeField()
    modified = models.DateTimeField()
    active = models.IntegerField()

    class Meta:
        db_table = u'admin'
        app_label = 'pfxadmin_migrate'
        managed = False


class Alias(models.Model):
    address = models.CharField(max_length=255, primary_key=True)
    goto = models.TextField()
    domain = models.CharField(max_length=255)
    created = models.DateTimeField()
    modified = models.DateTimeField()
    active = models.IntegerField()

    class Meta:
        db_table = u'alias'
        app_label = 'pfxadmin_migrate'
        managed = False


class AliasDomain(models.Model):
    alias_domain = models.CharField(max_length=255, primary_key=True)
    target_domain = models.CharField(max_length=255)
    created = models.DateTimeField()
    modified = models.DateTimeField()
    active = models.IntegerField()

    class Meta:
        db_table = u'alias_domain'
        app_label = 'pfxadmin_migrate'
        managed = False


class Config(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(unique=True, max_length=60)
    value = models.CharField(max_length=60)

    class Meta:
        db_table = u'config'
        app_label = 'pfxadmin_migrate'
        managed = False


class Domain(models.Model):
    domain = models.CharField(max_length=255, primary_key=True)
    description = models.CharField(max_length=255)
    aliases = models.IntegerField()
    mailboxes = models.IntegerField()
    maxquota = models.BigIntegerField()
    quota = models.BigIntegerField()
    transport = models.CharField(max_length=255)
    backupmx = models.IntegerField()
    created = models.DateTimeField()
    modified = models.DateTimeField()
    active = models.IntegerField()
    admins = models.ManyToManyField(Admin, through='DomainAdmins')

    class Meta:
        db_table = u'domain'
        app_label = 'pfxadmin_migrate'
        managed = False


class DomainAdmins(models.Model):
    username = models.ForeignKey(Admin, db_column='username')
    domain = models.ForeignKey(Domain, db_column='domain')
    created = models.DateTimeField(primary_key=True)
    active = models.IntegerField()

    class Meta:
        db_table = u'domain_admins'
        app_label = 'pfxadmin_migrate'
        managed = False


class Fetchmail(models.Model):
    id = models.IntegerField(primary_key=True)
    mailbox = models.CharField(max_length=255)
    src_server = models.CharField(max_length=255)
    src_auth = models.CharField(max_length=33, blank=True)
    src_user = models.CharField(max_length=255)
    src_password = models.CharField(max_length=255)
    src_folder = models.CharField(max_length=255)
    poll_time = models.IntegerField()
    fetchall = models.IntegerField()
    keep = models.IntegerField()
    protocol = models.CharField(max_length=12, blank=True)
    usessl = models.IntegerField()
    extra_options = models.TextField(blank=True)
    returned_text = models.TextField(blank=True)
    mda = models.CharField(max_length=255)
    date = models.DateTimeField()

    class Meta:
        db_table = u'fetchmail'
        app_label = 'pfxadmin_migrate'
        managed = False


class Log(models.Model):
    timestamp = models.DateTimeField()
    username = models.CharField(max_length=255)
    domain = models.CharField(max_length=255)
    action = models.CharField(max_length=255)
    data = models.TextField()

    class Meta:
        db_table = u'log'
        app_label = 'pfxadmin_migrate'
        managed = False


class Mailbox(models.Model):
    username = models.CharField(max_length=255, primary_key=True)
    password = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    maildir = models.CharField(max_length=255)
    quota = models.BigIntegerField()
    local_part = models.CharField(max_length=255)
    domain = models.CharField(max_length=255)
    created = models.DateTimeField()
    modified = models.DateTimeField()
    active = models.IntegerField()

    class Meta:
        db_table = u'mailbox'
        app_label = 'pfxadmin_migrate'
        managed = False


class Quota(models.Model):
    username = models.CharField(max_length=255, primary_key=True)
    path = models.CharField(max_length=100, primary_key=True)
    current = models.BigIntegerField(null=True, blank=True)

    class Meta:
        db_table = u'quota'
        app_label = 'pfxadmin_migrate'
        managed = False


class Quota2(models.Model):
    username = models.CharField(max_length=100, primary_key=True)
    bytes = models.BigIntegerField()
    messages = models.IntegerField()

    class Meta:
        db_table = u'quota2'
        app_label = 'pfxadmin_migrate'
        managed = False


class Vacation(models.Model):
    email = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    cache = models.TextField()
    domain = models.CharField(max_length=255)
    created = models.DateTimeField()
    active = models.IntegerField()

    class Meta:
        db_table = u'vacation'
        app_label = 'pfxadmin_migrate'
        managed = False


class VacationNotification(models.Model):
    on_vacation = models.ForeignKey(Vacation, db_column='on_vacation')
    notified = models.CharField(max_length=255, primary_key=True)
    notified_at = models.DateTimeField()

    class Meta:
        db_table = u'vacation_notification'
        app_label = 'pfxadmin_migrate'
        managed = False

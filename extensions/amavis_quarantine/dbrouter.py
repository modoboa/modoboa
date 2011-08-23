class AmavisRouter(object):
    """A router to control all database operations on models in
    the amavis_quarantine application"""

    def db_for_read(self, model, **hints):
        "Point all operations on amavis_quarantine models to 'amavis'"
        if model._meta.app_label == 'amavis_quarantine':
            return 'amavis'
        return None

    def db_for_write(self, model, **hints):
        "Point all operations on amavis_quarantine models to 'amavis'"
        if model._meta.app_label == 'amavis_quarantine':
            return 'amavis'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        "Allow any relation if a model in amavis_quarantine is involved"
        if obj1._meta.app_label == 'amavis_quarantine' \
                or obj2._meta.app_label == 'amavis_quarantine':
            return True
        return None

    def allow_syncdb(self, db, model):
        "Make sure the amavis_quarantine app only appears on the 'amavis' db"
        if db == 'amavis':
            return model._meta.app_label == 'amavis_quarantine'
        elif model._meta.app_label == 'amavis_quarantine':
            return False
        return None

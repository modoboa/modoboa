class AmavisRouter:
    """A router to control all database operations on models in
    the amavis application"""

    def db_for_read(self, model, **hints):
        """Point all operations on amavis models to 'amavis'."""
        if model._meta.app_label == "amavis":
            return "amavis"
        return None

    def db_for_write(self, model, **hints):
        """Point all operations on amavis models to 'amavis'."""
        if model._meta.app_label == "amavis":
            return "amavis"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        """Allow any relation if a model in amavis is involved."""
        if obj1._meta.app_label == "amavis" or obj2._meta.app_label == "amavis":
            return True
        return None

    def allow_migrate(self, db, app_label, model=None, **hints):
        """
        Make sure the auth app only appears in the 'amavis'
        database.
        """
        if app_label == "amavis":
            # modoboa_amavis migrations should be created in the amavis
            # database.
            return db == "amavis"
        elif db == "amavis":
            # Don't create non modoboa_amavis migrations in the amavis database.
            return False
        return None

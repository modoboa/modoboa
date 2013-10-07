from django.conf import settings

user_model_name = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
user_table_name = "auth_user" if user_model_name == "auth.User" else "core_user"

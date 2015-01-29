"""Additional functions available for migration scripts."""


def add_permissions_to_group(apps, groupname, permissions):
    """Add the specified permissions to a django group."""
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    grp = Group.objects.get(name=groupname)
    for appname, modelname, permname in permissions:
        ct = ContentType.objects.get_by_natural_key(
            appname, modelname)
        grp.permissions.add(
            Permission.objects.get(content_type=ct, codename=permname)
        )

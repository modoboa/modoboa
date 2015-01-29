"""Additional functions available for migration scripts."""


def add_permissions_to_group(apps, group, permissions):
    """Add the specified permissions to a django group."""
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    if isinstance(group, basestring):
        Group = apps.get_model("auth", "Group")
        group = Group.objects.get(name=group)

    for appname, modelname, permname in permissions:
        ct = ContentType.objects.get_by_natural_key(
            appname, modelname)
        group.permissions.add(
            Permission.objects.get(content_type=ct, codename=permname)
        )

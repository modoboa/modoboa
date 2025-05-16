"""Form management utilities."""


class UserKwargModelFormMixin:
    """Simple form mixin to add support for user kwargs in constructor."""

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

"""Views utilities."""


class UserFormKwargsMixin:
    """A mixin to automatically add a user arg to form instantiation."""

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"user": self.request.user})
        return kwargs

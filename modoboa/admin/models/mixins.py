"""Admin model mixins."""

from modoboa.policyd.utils import get_message_counter


class MessageLimitMixin:
    """A mixin to add message limit support."""

    @property
    def message_counter_key(self):
        raise NotImplementedError

    @property
    def sent_messages(self):
        """Return number of sent messages for the current day."""
        if self.message_limit is None:
            return None
        return (
            self.message_limit - get_message_counter(self.message_counter_key)
        )

    @property
    def sent_messages_in_percent(self):
        """Return number of sent messages as a percentage."""
        if self.message_limit is None:
            return None
        return int(self.sent_messages / float(self.message_limit) * 100)

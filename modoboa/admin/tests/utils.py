"""Test utilities."""


class FakeDNSAnswer(object):
    """Fake answer."""

    def __init__(self, exchange):
        self.exchange = exchange

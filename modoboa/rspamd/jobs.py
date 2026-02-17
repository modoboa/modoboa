"""Async jobs."""

import logging

from modoboa.admin import models
from modoboa.parameters import tools as param_tools

logger = logging.getLogger("modoboa.jobs")


class MapsUpdater:

    def __init__(self) -> None:
        self.modified_selector_file = False
        self.modified_key_path_file = False
        self.config = dict(param_tools.get_global_parameters("rspamd"))
        self.dkim_path_map: dict[str, str] = {}
        self.selector_map: dict[str, str] = {}

    def load_files(self):
        if not self.config["key_map_path"] or not self.config["selector_map_path"]:
            logger.error(
                "path map path and/or selector map path "
                "not set in modoboa rspamd settings."
            )
            return False

        try:
            with open(self.config["key_map_path"]) as f:
                for line in f:
                    domain_name, path = line.split()
                    self.dkim_path_map[domain_name] = path.replace("\n", "")
        except FileNotFoundError:
            pass
        try:
            with open(self.config["selector_map_path"]) as f:
                for line in f:
                    domain_name, selector = line.split()
                    self.selector_map[domain_name] = selector
        except FileNotFoundError:
            pass
        return True

    def manage_domain(self, domain_instance):
        domain_name = domain_instance.name
        selector_entry = self.selector_map.get(domain_name)
        dkim_path_entry = self.dkim_path_map.get(domain_name)
        if not domain_instance.enable_dkim:
            if selector_entry is not None:
                self.selector_map.pop(domain_name)
                self.modified_selector_file = True
            if dkim_path_entry is not None:
                self.dkim_path_map.pop(domain_name)
                self.modified_key_path_file = True
            return

        # modify selector map
        condition = (
            selector_entry is None
            or selector_entry != domain_instance.dkim_key_selector
        )
        if condition:
            self.selector_map[domain_name] = domain_instance.dkim_key_selector
            self.modified_selector_file = True

        # modify dkim path map
        condition = (
            dkim_path_entry is None
            or dkim_path_entry != domain_instance.dkim_private_key_path
        )
        if condition:
            self.dkim_path_map[domain_name] = domain_instance.dkim_private_key_path
            self.modified_key_path_file = True

    def run(self, domains):
        """Entry point."""
        if not self.load_files():
            return

        for domain in domains:
            self.manage_domain(domain)

        if self.modified_selector_file:
            with open(self.config["selector_map_path"], "w") as f:
                for domain_name, selector in self.selector_map.items():
                    f.write(f"{domain_name} {selector}\n")
        if self.modified_key_path_file:
            with open(self.config["key_map_path"], "w") as f:
                for domain_name, key_path in self.dkim_path_map.items():
                    f.write(f"{domain_name} {key_path}\n")


def update_rspamd_maps(domain_ids: list[int]) -> None:
    """Launch map files update."""
    domains = models.Domain.objects.filter(id__in=domain_ids)
    MapsUpdater().run(domains)

from . import ImporterBackend


OUTLOOK_COLUMNS = [
    "First Name",
    "Middle Name",
    "Last Name",
    "Company",
    "E-mail Address",
    "Business Phone",
    "Business Street",
    "Business Street 2",
    "Business City",
    "Business State",
    "Business Postal Code",
]


class OutlookBackend(ImporterBackend):
    """Outlook contact importer backend."""

    name = "outlook"
    field_names = {
        "first_name": "",
        "last_name": "Last Name",
        "company": "Company",
        "address": "",
        "city": "Business City",
        "zipcode": "Business Postal Code",
        "state": "Business State",
    }

    @classmethod
    def detect_from_columns(cls, columns):
        return set(OUTLOOK_COLUMNS).issubset(columns)

    def get_first_name(self, values: dict) -> str:
        result = values["First Name"]
        if values["Middle Name"]:
            result += f" {values['Middle Name']}"
        return result

    def get_address(self, values: dict) -> str:
        result = values["Business Street"]
        if values["Business Street 2"]:
            result += f" {values['Business Street 2']}"
        return result

    def get_email(self, values: dict) -> str:
        return values["E-mail Address"]

    def get_phone_number(self, values: dict) -> str:
        return values["Business Phone"]

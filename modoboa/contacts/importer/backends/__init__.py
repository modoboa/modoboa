from modoboa.contacts import models, tasks


class ImporterBackend:
    """Base class of all importer backends."""

    name: str

    field_names: dict = {}

    def __init__(self, addressbook: models.AddressBook):
        self.addressbook = addressbook

    @classmethod
    def detect_from_columns(cls, columns: list) -> bool:
        raise NotImplementedError

    def get_email(self, values: dict):
        return None

    def get_phone_number(self, values: dict):
        return None

    def import_contact(self, row) -> models.Contact:
        contact = models.Contact(addressbook=self.addressbook)
        for local_name, row_name in self.field_names.items():
            method_name = f"get_{local_name}"
            if hasattr(self, method_name):
                value = getattr(self, method_name)(row)
            else:
                value = row[row_name]
            setattr(contact, local_name, value)
        contact.save()
        if self.get_email(row):
            models.EmailAddress.objects.create(
                contact=contact, address=self.get_email(row), type="work"
            )
        if self.get_phone_number(row):
            models.PhoneNumber.objects.create(
                contact=contact, number=self.get_phone_number(row), type="work"
            )
        return contact

    def proceed(self, rows: list, carddav_password: str = None):
        for row in rows:
            contact = self.import_contact(row)
            if carddav_password:
                # FIXME: refactor CDAV tasks to allow connection from
                # credentials and not only request
                clt = tasks.get_cdav_client(
                    self.addressbook,
                    self.addressbook.user.email,
                    carddav_password,
                    True,
                )
                path, etag = clt.upload_new_card(contact.uid, contact.to_vcard())
                contact.etag = etag
                contact.save(update_fields=["etag"])

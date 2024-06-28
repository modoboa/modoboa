from fido2.webauthn import (
    PublicKeyCredentialRpEntity,
    PublicKeyCredentialUserEntity,
    AttestedCredentialData,
    UserVerificationRequirement,
)
from fido2.server import Fido2Server
from fido2.utils import websafe_decode, websafe_encode
import fido2.features

from django.utils import timezone

from modoboa.core.models import User, UserFidoKeys


def set_json_mapping():
    try:
        fido2.features.webauthn_json_mapping.enabled = True
    except ValueError:
        pass


def create_fido2_server():
    rp = PublicKeyCredentialRpEntity(name="Demo server", id="localhost")
    return Fido2Server(rp)


def get_creds_from_user(user_id):
    return [
        AttestedCredentialData(websafe_decode(uf.credential_data))
        for uf in UserFidoKeys.objects.filter(user=user_id)
    ]


def begin_registration(request):
    set_json_mapping()
    server = create_fido2_server()
    options, state = server.register_begin(
        PublicKeyCredentialUserEntity(
            id=request.user.pk,
            name=request.user.username.encode("utf-8"),
            display_name=request.user.username,
        ),
        get_creds_from_user(request.user.pk),
        user_verification=UserVerificationRequirement.DISCOURAGED,
        extensions={"credentialProtectionPolicy": "userVerificationOptional"},
    )
    request.session["fido2_state"] = state
    return options


def end_registration(data, fido2_state, user_id):
    set_json_mapping()
    server = create_fido2_server()
    auth_data = server.register_complete(fido2_state, data)
    return websafe_encode(auth_data.credential_data)


def begin_authentication(user_id: int):
    set_json_mapping()
    server = create_fido2_server()
    return server.authenticate_begin(get_creds_from_user(user_id))


def end_authentication(user: User, state: str, data: dict):
    set_json_mapping()
    server = create_fido2_server()
    # FIXME: review the next function...
    credentials = get_creds_from_user(user.pk)
    result = server.authenticate_complete(
        state,
        credentials,
        data,
    )
    for key in user.userfidokeys_set.all():
        cred = AttestedCredentialData(websafe_decode(key.credential_data))
        if cred.credential_id == result.credential_id:
            key.last_used = timezone.now()
            key.use_count += 1
            key.save()

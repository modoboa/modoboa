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

from modoboa.core.models import User, UserFidoKey


def set_json_mapping():
    try:
        fido2.features.webauthn_json_mapping.enabled = True
    except ValueError:
        pass


def create_fido2_server(rp_id: str) -> Fido2Server:
    rp = PublicKeyCredentialRpEntity(name="Modoboa", id=rp_id)
    return Fido2Server(rp)


def get_creds_from_user(user_id: int) -> dict:
    return {
        key: AttestedCredentialData(websafe_decode(key.credential_data))
        for key in UserFidoKey.objects.filter(user=user_id)
    }


def begin_registration(request):
    set_json_mapping()
    server = create_fido2_server(request.localconfig.site.domain)
    options, state = server.register_begin(
        PublicKeyCredentialUserEntity(
            id=request.user.pk,
            name=request.user.username.encode("utf-8"),
            display_name=request.user.username,
        ),
        list(get_creds_from_user(request.user.pk).values()),
        user_verification=UserVerificationRequirement.DISCOURAGED,
        extensions={"credentialProtectionPolicy": "userVerificationOptional"},
    )
    request.session["fido2_state"] = state
    return options


def end_registration(request):
    set_json_mapping()
    server = create_fido2_server(request.localconfig.site.domain)
    auth_data = server.register_complete(
        request.session.pop("fido2_state"), request.data
    )
    return websafe_encode(auth_data.credential_data)


def begin_authentication(request, user_id: int):
    set_json_mapping()
    server = create_fido2_server(request.localconfig.site.domain)
    return server.authenticate_begin(list(get_creds_from_user(user_id).values()))


def end_authentication(user: User, state: str, data: dict, rp_id: str):
    set_json_mapping()
    server = create_fido2_server(rp_id)
    credentials = get_creds_from_user(user.pk)
    result = server.authenticate_complete(
        state,
        list(credentials.values()),
        data,
    )
    for key, cred in credentials.items():
        if cred.credential_id == result.credential_id:
            key.last_used = timezone.now()
            key.use_count += 1
            key.save()

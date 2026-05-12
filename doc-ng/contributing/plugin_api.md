---
title: plugin development guide for modoboa
description: Discover how to develop a plugin for modoboa to extend functionnalities
head:
  - - meta
    - name: 'keywords'
      content: 'modoboa, plugin, extension, api, navigation, Django signals, module federation, vue'
---

# Create a new plugin

## Introduction

Modoboa offers a plugin API to expand its capabilities.

The current implementation provides the following possibilities:

- Expand backend navigation, register callbacks, and extend administrative
  objects through [Django signals](https://docs.djangoproject.com/en/5.2/topics/signals/).
- Add fields to the REST API by attaching to dedicated serializer signals
  (e.g. `DomainSerializer`).
- Inject menu entries, routes, and UI components into the Vue 3 frontend
  via a federated remote that the host loads at runtime.

::: tip
Plugins are nothing more than Django applications with an extra piece of
code that integrates them into Modoboa. A plugin **may** ship a frontend
bundle, but it is not required: pure backend plugins remain perfectly
valid.
:::

The `modo_extension.py` file contains a complete description of the plugin:

- Admin and user parameters
- Custom menu entries
- Frontend manifest (routes, UI extensions, federated remote)

The following subsections describe the plugin architecture and explain
how you can create your own.

## The required glue

To create a new plugin, just start a new django application like this
(into Modoboa's directory):

```shell
$ python manage.py startapp
```

Then, you need to register this application using the provided API.

Just copy/paste the following example into the `modo_extension.py` file of the future extension:

```python
from modoboa.core.extensions import ModoExtension, exts_pool


class MyExtension(ModoExtension):
    """My custom Modoboa extension."""

    name = "myext"
    label = "My Extension"
    version = "0.1"
    description = "A description"
    url = "myext_root_location" # optional, name is used if not defined

    def load(self):
        """This method is called when Modoboa loads available and activated plugins.

        Declare parameters and register events here.
        """
        pass

    def load_initial_data(self):
        """Optional: provide initial data for your extension here."""
        pass

exts_pool.register_extension(MyExtension)
```

Once done, simply add your extension's module name to the `MODOBOA_APPS`
variable located inside `settings.py`.

Finally, run the following commands:

```shell
$ python manage.py migrate
$ python manage.py load_initial_data
$ python manage.py collectstatic
```

### Parameters

A plugin can declare its own parameters. There are two levels available:

* `Global` parameters: used to configure the plugin, editable inside
  the *Admin > Settings > Parameters* page
* `User` parameters: per-user parameters (or preferences), editable
  inside the *Options > Preferences* page

#### Playing with parameters

Parameters are defined using [Django forms](https://docs.djangoproject.com/en/1.9/topics/forms/)
and Modoboa adds two special forms you can inherit depending on the level of parameter(s) you want to add:

* `modoboa.parameters.forms.AdminParametersForm`: for general parameters
* `modoboa.parameters.forms.UserParametersForm`: for user parameters

To register new parameters, add the following line into the `load` method of your plugin class:

```python
from modoboa.parameters import tools as param_tools
param_tools.registry.add(LEVEL, YourForm, ugettext_lazy("Title"))
```
Replace:

* `LEVEL` (str):  `"global"` or `"user"`.

### Custom role permissions

Modoboa uses Django's internal permission system.

Administrative roles are nothing more than groups (`Group` instances).

An extension can add new permissions to a group by listening to the `extra_role_permissions` signal. Here is an example:

``` python
from django.dispatch import receiver
from modoboa.core import signals as core_signals

PERMISSIONS = {
    "Resellers": [
        ("relaydomains", "relaydomain", "add_relaydomain"),
        ("relaydomains", "relaydomain", "change_relaydomain"),
        ("relaydomains", "relaydomain", "delete_relaydomain"),
        ("relaydomains", "service", "add_service"),
        ("relaydomains", "service", "change_service"),
        ("relaydomains", "service", "delete_service")
    ]
}

@receiver(core_signals.extra_role_permissions)
def extra_role_permissions(sender, role, **kwargs):
   """Add permissions to the Resellers group."""
   return constants.PERMISSIONS.get(role, [])
```

## Extending the `DomainSerializer`

Plugins can hook into the REST `DomainSerializer` to add fields, expose
extra read-only data, and react to create/update side effects. Four
signals from `modoboa.admin.signals` cover the full lifecycle.

| Signal | Provides | Receivers return |
|---|---|---|
| `extra_domain_serializer_fields` | (nothing) | `dict[str, serializers.Field]` — declarative fields merged into the serializer (typically `write_only=True`). |
| `extra_domain_serializer_data` | `domain` | `dict[str, Any]` — merged into the JSON representation (read side). |
| `domain_post_create_via_api` | `domain`, `plugin_data`, `request` | — (side-effects only). |
| `domain_post_update_via_api` | `domain`, `plugin_data`, `request` | — (side-effects only). |

`plugin_data` is the dict of values popped out of `validated_data` for
the fields contributed by `extra_domain_serializer_fields`, so plugins
get exactly what was submitted without polluting the `Domain` model.

::: warning Read side is not automatic
Fields declared via `extra_domain_serializer_fields` are not read back
automatically — DRF would try to look the attribute up on the
`Domain` instance, fail with `AttributeError`, and silently drop the
field. Use `write_only=True` for input fields and connect to
`extra_domain_serializer_data` to provide the read value.
:::

Example — a plugin that attaches a free-form `billing_reference`
string to a domain, stored in its own model:

```python
from django.dispatch import receiver
from rest_framework import serializers

from modoboa.admin import signals as admin_signals
from modoboa.admin.api.v2 import serializers as admin_serializers

from . import models  # plugin-local model: DomainBilling(domain, reference)


@receiver(admin_signals.extra_domain_serializer_fields,
          sender=admin_serializers.DomainSerializer)
def add_billing_reference_field(sender, **kwargs):
    return {
        "billing_reference": serializers.CharField(
            required=False,
            allow_null=True,
            allow_blank=True,
            write_only=True,
        ),
    }


@receiver(admin_signals.extra_domain_serializer_data,
          sender=admin_serializers.DomainSerializer)
def add_billing_reference_data(sender, domain, **kwargs):
    billing = models.DomainBilling.objects.filter(domain=domain).first()
    return {"billing_reference": billing.reference if billing else None}


@receiver(admin_signals.domain_post_create_via_api,
          sender=admin_serializers.DomainSerializer)
def save_billing_reference(sender, domain, plugin_data, request, **kwargs):
    reference = (plugin_data.get("billing_reference") or "").strip()
    if not reference:
        return
    models.DomainBilling.objects.update_or_create(
        domain=domain, defaults={"reference": reference}
    )
```

## Frontend extension points

A plugin extends the Vue 3 frontend by declaring its UI contribution on
the `ModoExtension` subclass. The host fetches the aggregated manifest
from `GET /api/v2/frontend/plugins/` and wires everything up at startup
through [Module Federation](https://module-federation.io/).

The following class attributes are recognized on `ModoExtension`:

| Attribute | Purpose |
|---|---|
| `frontend_menu_entries: list[dict]` | Items injected into the host navigation, grouped by category. |
| `frontend_routes: list[dict]` | Vue Router routes loaded into the host router at startup. |
| `frontend_remote: dict \| None` | Federated remote descriptor (where the host loads your bundle from). |
| `frontend_ui_extensions: dict[str, list[dict]]` | Items inserted at named extension points throughout the UI. |

### Declaring the remote

`frontend_remote` describes the federated entry the host should load:

```python
class MyExtension(ModoExtension):
    name = "myext"
    label = "My Extension"
    frontend_remote = {
        "name": "myext",
        # In production, ship the build under STATIC_URL and let
        # ManifestStaticFilesStorage handle the hashed filename:
        "static_path": "myext/remoteEntry.js",
        # In dev, point directly at the plugin's preview server:
        # "url": "https://localhost:5174/remoteEntry.js",
        "format": "esm",
    }
```

- `url` — used verbatim. Use for absolute CDN/dev-server URLs.
- `static_path` — relative to `STATIC_URL`, resolved through Django's
  `static()` helper so hashed filenames produced by
  `ManifestStaticFilesStorage` are picked up automatically.
- `url` takes precedence over `static_path` if both are set.

### Menu entries

```python
frontend_menu_entries = [
    {
        "label": "My Extension",
        "icon": "mdi-puzzle",
        "to": "MyExtensionRoute",   # route name (preferred)
        "url": "https://...",        # OR an external URL
        "category": "admin",         # admin | user | account
        "roles": ["SuperAdmins"],   # optional role gate
        "children": [...],           # nested submenu items
    }
]
```

### Routes

```python
frontend_routes = [
    {
        "name": "MyExtensionRoute",
        "path": "myext",
        "component": "./MyExtensionView",   # exposed module name in your remote
        "parent": "AdminLayout",             # mount under an existing route…
        "meta": {...},
        "props": {...},
        "children": [...],
    }
]
```

`component` is resolved against the plugin's federated remote — the
host calls `loadRemote("<remote.name>/<component>")` lazily. If
`parent` is set, the route is added as a child of that named route in
the host router; otherwise it is added at the top level.

### UI extension points

`frontend_ui_extensions` is keyed by extension-point id. Each item is a
loose dict; the host passes through any extra keys so the consuming
extension point can interpret them.

Common fields per item:

- `name` — unique id (required).
- `title` — display label, where applicable.
- `component` — module path on the plugin remote (e.g. `"./MyTab"`).
- `applies_to` — optional list of domain types (`"domain"`, `"relaydomain"`); empty/missing means "any".
- `position`, `props`, `summary` — interpreted by the extension point.

The extension points currently exposed by the host:

| Extension point id | Where it renders |
|---|---|
| `domain.creation_form.steps` | Extra step(s) appended to the domain creation wizard. |
| `domain.edit_form.panels` | Extra panels in the domain edit form. |
| `domain.detail.general.blocks` | Blocks added to the *General* tab of the domain detail view (set `column: "left"` or `"right"`). |
| `domain.detail.tabs` | Top-level tabs added to the domain detail view. |

Example:

```python
frontend_ui_extensions = {
    "domain.detail.tabs": [
        {
            "name": "myext.billing",
            "title": "Billing",
            "component": "./BillingTab",
            "applies_to": ["domain"],
        }
    ],
    "domain.edit_form.panels": [
        {
            "name": "myext.billing_panel",
            "title": "Billing",
            "component": "./BillingPanel",
        }
    ],
}
```

### Building the remote with Module Federation

The host expects an ESM federated build. The plugin's `vite.config.js`
should use [`@module-federation/vite`](https://github.com/module-federation/vite)
and pin shared dependencies as singletons matching the host's pins:

```js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { federation } from '@module-federation/vite'

export default defineConfig({
  plugins: [
    vue(),
    federation({
      name: 'myext',
      filename: 'remoteEntry.js',
      dts: false,
      exposes: {
        './BillingTab': './src/BillingTab.vue',
        './BillingPanel': './src/BillingPanel.vue',
      },
      // Consume host-shared singletons (host exposes the same set):
      shared: {
        vue: { singleton: true, requiredVersion: '^3.4.0' },
        'vue-router': { singleton: true, requiredVersion: '^4.0.0' },
        pinia: { singleton: true, requiredVersion: '^3.0.0' },
        vuetify: { singleton: true, requiredVersion: '^4.0.0' },
        'vue3-gettext': { singleton: true, requiredVersion: '^4.0.0-beta.1' },
      },
    }),
  ],
  build: { target: 'esnext', minify: false },
})
```

The host additionally exposes the following modules under the
`modoboa_host` remote, so plugins can reuse host stores and components
instead of importing their own copies:

- `modoboa_host/stores` — the shared pinia stores (`useAuthStore`,
  `useGlobalStore`, `usePluginsStore`, …)
- `modoboa_host/repository` — the configured axios instance.
- `modoboa_host/MenuItems` — the host navigation component.
- `modoboa_host/ConfirmDialog` — the host confirmation dialog.

::: warning Federation does not work with `vite dev`
`@module-federation/vite` only generates `remoteEntry.js` during the
production build. While developing a plugin, run `yarn build && yarn
preview` (HTTPS) — the host's federation runtime cannot consume the
dev server's transformed module graph.
:::

### Shipping the build

For production, run `yarn build` and place the output under a Django
static folder so `collectstatic` picks it up. With the default
`static_path` setting, the bundle is reachable at
`STATIC_URL + "myext/remoteEntry.js"` and benefits from the hashed
filenames produced by `ManifestStaticFilesStorage`.

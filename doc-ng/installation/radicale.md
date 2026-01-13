---
title: manual step to install radicale component on modoboa
description: This guide describe how to install radicale on the modoboa platform
head:
  - - meta
    - name: 'keywords'
      content: 'modoboa, installation, radicale, oauth2' 
---

# Radicale

This page is displaying how to install and use radicale when either
having installed modoboa manually or with the dedicated installer.

## OAuth 2 authentication 

::: tip
These steps are automatic if you use an up-to-date modoboa-installer to
install/upgrade.
:::

### Preparing the usage of radicale (manual install only)

::: warning
It is assumed you have not installed in the past radicale from your
package manager and your modoboa installation is working correctly. 

If so, you may skip this section and proceed to the next one. 
:::

You will need
to create directories for the radicale user, needed files and set-up the
account (location may change depending on your OS and initial set-up).

``` shell
$ sudo mkdir /var/lib/radicale /etc/radicale
$ sudo touch /etc/radicale/{rights,config}
$ sudo adduser --system --home /var/lib/radicale/ --no-create-home --gecos "Radicale CalDAV server" --group --disabled-password --quiet radicale
$ sudo chown -R radicale /etc/radicale
$ sudo chown /var/lib/radicale
```

### Creation of the virtual environment (manual install only)

``` shell
$ sudo -u radicale virtualenv /var/lib/radicale/env
```

### Installing radicale oauth plugin

You need to install `radicale-modoboa-auth-oauth2` python package inside
radicale venv. If you used the installer you can use the following
commands:

``` shell
$ sudo -u radicale -i bash
$ cd ~
$ env/bin/pip install radicale-modoboa-auth-oauth2
```

For manual installations, this will do the job:

``` shell
$ sudo -u radicale /var/lib/radicale/env/bin/pip install radicale-modoboa-auth-oauth2
```

Please note because the plugin offered by modoboa's team is listing
radicale as a dependency you do not need to explicitely install
radicale.

### Oauth application creation

You first need to register Radicale as an authorized consumer of the
OAuth2 authentication service provided by Modoboa. To do so, create an
application with the following commands:

``` shell
$ cd <modoboa_instance_path>
$ python manage.py createapplication --name=Radicale --skip-authorization --client-id=radicale confidential client-credentials
```

On success, you should see an output similar to:

```console
New application Radicale created successfully.
client_secret: XXXX
```

To enable OAuth2 authentication in Radicale, edit the `/etc/radicale/config` file
and update the [type] in [\[auth\]] to:
```txt
type = radicale_modoboa_auth_oauth2
````

Then, add the following line in \`\[auth\]\`:

```txt
oauth2_introspection_endpoint = https://radicale:<client_secret>@<hostname of your server>/api/o/introspect/
````

Replace `<client_secret>` with the value you obtained earlier.

Your `/etc/radicale/config`{.interpreted-text role="file"} should look
like this (listening address and port may vary):

```ini
[server]
hosts = 0.0.0.0:5232,[::]:5232

[auth]
type = radicale_modoboa_auth_oauth2
oauth2_introspection_endpoint = https://radicale:<client_secret>@<hostname of your server>/api/o/introspect/

[rights]
type = from_file
file = /etc/radicale/rights

[storage]
filesystem_folder = /var/lib/radicale/collections
````

With that set-up, radicale should be working when managing calendars
through modoboa's web interface but [not]{#not}\_ when using other
clients like Thunderbird.

### Modifications for using external clients (optional)

To ensure other clients can identify, you need to modify radicale by
adding in the config file under the \[auth\] section:

```txt
dovecot_socket = /run/dovecot/auth-radicale
```

and in `10-master.conf` for dovecot:

```txt
unix_listener auth-radicale {
    mode = 0660
    user = radicale
    group = dovecot        
}
```

Then, restart both `modoboa` and `radicale` to enjoy managing calendars (ICS type) with your favorite client.

### Reverse proxy for radicale (optional)

At this stage, no encryption is provided, and you may use a reverse proxy as described in

[Radicale's documentation](https://radicale.org/v3.html#reverse-proxy).
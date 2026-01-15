# Configuration

## Online parameters

Modoboa provides online panels to modify internal parameters. There are
two available levels:

- **Application level**: global parameters, define how the application
  behaves. Available at `Modoboa > Parameters`
- **User level**: per user customization. Available at `User > Settings >
  Preferences`
Regardless level, parameters are displayed using tabs, each tab
corresponding to one application.

## General parameters {#admin-params}

The *admin* application exposes several parameters, they are presented
below:


| Name           | Tab           | Description                    | Default Value    |
| :-:            | :-:           | :--                            | :-:          |
| Authentication type | General       | The backend used for authentication          | Local        |
| Default password  scheme     | General  passwords     | Scheme used to crypt mailbox   | sha512crypt  |
| Rounds         | General       | Number of rounds (only used by [sha256crypt] and [sha512crypt]).  Must be between 1000 and 999999999, inclusive. | 70000 |
| Secret key     | General       | A key used to encrypt users password in sessions  | random value |
| Sender address | General       | Email address used to send notifications.    |              |
| Enable communication | General | Enable communication with Modoboa public API | yes    |
| Check new versions | General | Automatically checks if a  newer version is available | yes |
| Send statistics | General | Send statistics to Modoboa public API (counters and used extensions) | yes |
| Top notifications check interval | General | Interval between two top notification checks (in seconds)  | 30 |
| Maximum log record age | General       | The maximum age in days of a log record   | 365 |
| Items per page | General | Number of displayed items per page | 30 |
| Default top redirection | General | The default redirection used when no application is specified | userprefs |
| Enable MX checks | Admin | Check that every domain has a valid MX record | yes |
| Valid MXs | Admin | A list of IP or network address every MX should match. A warning will be sent if a record does not respect this it. |  |
| Enable DNSBL checks  | Admin | Check every domain against major DNSBL providers   | yes |
| DKIM keys storage directory | Admin | Path to a directory where DKIM generated keys will be stored |              |
| Default DKIM key length  | Admin | The default size (in bits) for new keys | 2048 |
| Handle mailboxes on filesystem | Admin | Rename or remove mailboxes on the filesystem when they get renamed or removed within Modoboa | no |
| Mailboxes  owner    | Admin         | The UNIX account who owns mailboxes on the filesystem    | vmail |
| Default domain quota | Admin         | Default quota (in MB) applied to freshly created domains with no value specified. A value of 0 means no quota. | 0 |
| Automatic account removal     | Admin         | When a mailbox is removed, also remove the associated account | no |
| Automatic domain/mailbox creation    | Admin         | Create a domain and a mailbox when an account is automatically created | yes |

::: warning
If Dovecot is not running on the same host than Modoboa, you will have
to define which password schemes are supported.

To do so, open the `settings.py` file and add a `DOVECOT_SUPPORTED_SCHEMES` 
variable with the output of the command:
```shell
$ doveadm pw -l
```
:::

::: info

If you are not familiar with virtual domain hosting, you should take a look at 
[postfix's documentation](http://www.postfix.org/VIRTUAL_README.html). 

This [How to](https://help.ubuntu.com/community/PostfixVirtualMailBoxClamSmtpHowto)
also contains useful information.
:::

::: tip
A random secret key will be generated each time the *Parameters* page is
refreshed and until you save parameters at least once.
:::

::: info
Specific LDAP parameters are also available, see `LDAP
authentication <ldap_auth>`.
:::

### Media files

Modoboa uses a specific directory to upload files (ie. when the webmail
is in use) or to create ones (ex: graphical statistics). 

This directory is named `media` and is located inside modoboa's 
installation directory (called `modoboa_site` in this documentation).

To work properly, the system user which runs modoboa (`www-data`,
`apache`, whatever) must have write access to this directory.

### Customization

## Custom logo

You have the possibility to use a custom logo instead of the default one
on the login page and inside generated PDF documents.

To do so, open the `settings.py` file and add a `MODOBOA_CUSTOM_LOGO` variable.

This variable must contain the relative URL of your logo under `MEDIA_URL`.

For example:

``` python
MODOBOA_CUSTOM_LOGO = os.path.join(MEDIA_URL, "custom_logo.png")
```

Then copy your logo file into the directory indicated by `MEDIA_ROOT`.

You can also customize the logo(s) used in the frontend application
(left menu and creation forms).

To do so, copy the corresponding files inside the frontend directory
directly (defaults to `/srv/modoboa/instance/frontend`).

Then, edit the `config.json` file located in this very same directory and add the following variables:

```json
{
    "MENU_LOGO_PATH": "/cusrtom_logo.png",         // [!code focus]
    "CREATION_FORM_LOGO_PATH": "/custom_logo2.png" // [!code focus]
}
```

### Host configuration

::: tip
This section is only relevant when Modoboa handles mailboxes renaming
and removal from the filesystem, 
which requires that Dovecot is installed and running on this host.

If it is installed at a non-standard directory, 
paths to its binaries can be set in the `settings.py` file 
with the `DOVECOT_LOOKUP_PATH` and `DOVEADM_LOOKUP_PATH` variables.
:::

To manipulate mailboxes on the filesystem, you must allow the user who
runs Modoboa to execute commands as the user who owns mailboxes.

To do so, edit the `/etc/sudoers` file and add the following inside:

```txt
<user_that_runs_modoboa> ALL=(<mailboxes owner>) NOPASSWD: ALL
```

Replace values between `<>` by the ones you use.

### Time zone and language {#timezone_lang}

Modoboa is available in many languages.

To specify the default language to use, edit the `settings.py` file
and modify the `LANGUAGE_CODE` variable:

```python
LANGUAGE_CODE = 'fr' # or 'en' for english, etc.
```

::: tip
Each user has the possibility to define the language he prefers.
:::

In the same configuration file, specify the timezone to use 
by modifying the `TIME_ZONE` variable. For example:

```python
TIME_ZONE = 'Europe/Paris'
```

### Sessions management

Modoboa uses [Django's session framework](https://docs.djangoproject.com/en/dev/topics/http/sessions/?from=olddocs)
to store per-user information.

Few parameters need to be set in the `settings.py` configuration file to make Modoboa behave as expected:

```python
SESSION_EXPIRE_AT_BROWSER_CLOSE = False # Default value
```

This parameter is optional but you must ensure it is set to `False` (the default value).

The default configuration file provided by the `modoboa-admin.py` command is properly configured.

### Logging authentication

To trace login attempts to the web interface, Modoboa uses python 
[SysLogHandler](https://docs.python.org/3/library/logging.handlers.html#logging.handlers.SysLogHandler)

so you can see them in your syslog authentication log file ([/var/log/auth.log] in most cases).

Depending on your configuration, you may have to edit the `settings.py` file and add 
['address': \'/dev/log\'] to the logging section:

```python
'syslog-auth': {
    'class': 'logging.handlers.SysLogHandler',
    'facility': SysLogHandler.LOG_AUTH,
    'address': '/dev/log',
    'formatter': 'syslog'
},
```

### External authentication

## LDAP {#ldap_auth}

Modoboa supports external LDAP authentication using the following extra components:

* [Python LDAP client](http://www.python-ldap.org/)
* [Django LDAP authentication backend](http://pypi.python.org/pypi/django-auth-ldap)

If you want to use this feature, you must first install those components:

```shell
$ pip install python-ldap django-auth-ldap
```

Then, all you have to do is to modify the `settings.py` file. 

Add a new authentication backend to the [AUTHENTICATION_BACKENDS] variable, like this:

```python
AUTHENTICATION_BACKENDS = (
    'modoboa.lib.authbackends.LDAPBackend',
    # 'modoboa.lib.authbackends.LDAPSecondaryBackend',  # Useful for a fallback mechanism
    'django.contrib.auth.backends.ModelBackend',
)
```

Finally, go to **Modoboa > Parameters > General** and set *Authentication type* to LDAP.

From there, new parameters will appear to let you configure the way
Modoboa should connect to your LDAP server.

They are described just below:

| Name | Description | Default Value |
| :-: | :-- | :-: |
| Server address | The IP address of the DNS name of the LDAP server |localhost |
| Server port | The TCP port number used by the LDAP server | 389 |
| Use a secure connection | Use an SSL/TLS connection to access the LDAP server | no |
| Authentication method | Choose the authentication method to use | Direct bind |
| User DN template (direct bind mode)|  The template used to construct a user\'s DN. It should contain one placeholder (ie.`%(user)s`) | | 
| Bind BN | The distinguished name to use when binding to the LDAP server. Leave empty for an anonymous bind | |
| Bind password | The password to use when binding to the LDAP server (with \'Bind DN\') | |      
| Search base | The distinguished name of the search base | | 
| Search filter | An optional filter string (e.g. \'(objectClass=person)\'). In order to be valid, it must be enclosed in parentheses. | (mail=%(user)s) |
| Password attribute |  The attribute used to store user passwords |   userPassword |
| Active Directory | Tell if the LDAP server is an no Active Directory one | |                            
| Administrator groups | Members of those LDAP Posix groups will be created ad domain administrators. Use ';' characters to separate groups. | |   
| Group type | The type of group used by your PosixGroup LDAP directory. | |
| Groups search base | The distinguished name of the  search base used to find groups | | 
| Domain/mailbox creation | Automatically create a domain and a mailbox when a new user is created just after the first successful authentication. You will generally want to disable this feature when the relay domains extension is in use | yes |

::: tip
If you need additional parameters, you will find a detailed
documentation [here](http://packages.python.org/django-auth-ldap/).
:::

Once the authentication is properly configured, the users defined in
your `LDAP` directory will be able to connect to Modoboa, the associated
domain and mailboxes will be automatically created if needed.

The first time a user connects to Modoboa, a local account is created if
the `LDAP username` is a valid email address. By default, this account
belongs to the `SimpleUsers` group and it has a mailbox.

To automatically create domain administrators, you can use the
**Administrator groups** setting. If a LDAP user belongs to one the
listed groups, its local account will belong to the `DomainAdmins`
group. 

In this case, the username is not necessarily an email address.

Users will also be able to update their `LDAP password` directly from
Modoboa.

::: warning
Modoboa doesn't provide any synchronization mechanism once a user is
registered into the database. Any modification done from the directory
to a user account will not be reported to Modoboa (an email address
change for example). Currently, the only solution is to manually delete
the Modoboa record, it will be recreated on the next user login.
:::

## SMTP {#smtp_auth}

It is possible to use an existing SMTP server as an authentication
source. 

To enable this feature, edit the `settings.py` file and change the following setting:

``` python
AUTHENTICATION_BACKENDS = (
    'modoboa.lib.authbackends.SMTPBackend',
    'django.contrib.auth.backends.ModelBackend',
)
```

SMTP server location can be customized using the following settings:

``` python
AUTH_SMTP_SERVER_ADDRESS = 'localhost'
AUTH_SMTP_SERVER_PORT = 25
AUTH_SMTP_SECURED_MODE = None  # 'ssl' or 'starttls' are accepted
```

### LDAP synchronization {#ldap-sync}

Modoboa can synchronize accounts with an LDAP directory (tested with
OpenLDAP) but this feature is not enabled by default. 

To activate it, add `modoboa.ldapsync` to `MODOBOA_APPS` in the `settings.py` file:

```python
MODOBOA_APPS = (
    'modoboa',
    'modoboa.core',
    'modoboa.lib',
    'modoboa.admin',
    'modoboa.transport',
    'modoboa.relaydomains',
    'modoboa.limits',
    'modoboa.parameters',
    'modoboa.dnstools',
    'modoboa.ldapsync',
)
```

and enable it from the admin panel.

::: warning
Make sure to install additional `requirements <ldap_auth>`
otherwise it won't work.
:::

The following parameters are available and must be filled:

| Name | Description | Default Value |
| :-: | :-- | :-: |
| Enable LDAP synchronization | Control LDAP synchronization state | no |
| Bind DN | The DN of a user with write permission to create/update accounts | |                        
| Bind password | The associated password | |   
| Account DN template | The template used to build account DNs (must contain a %(user)s placeholder ) |

## Database maintenance

### Cleaning the logs table

Modoboa logs administrator specific actions into the database. A
clean-up script is provided to automatically remove oldest records. The
maximum log record age can be configured through the online panel.

To use it, you can setup a cron job to run every night:

```txt
0 0 * * * <modoboa_site>/manage.py cleanlogs
#
# Or like this if you use a virtual environment:
# 0 0 * * * <virtualenv path/bin/python> <modoboa_site>/manage.py cleanlogs
```

### Cleaning the session table

Django does not provide automatic purging. Therefore, it's your job to
purge expired sessions on a regular basis.

Django provides a sample clean-up script:

* `django-admin.py clearsessions`. That script deletes any session in the
  session table whose `expire_date` is in the past.

For example, you could setup a cron job to run this script every night:

```txt
0 0 * * * <modoboa_site>/manage.py clearsessions
#
# Or like this if you use a virtual environment:
# 0 0 * * * <virtualenv path/bin/python> <modoboa_site>/manage.py clearsessions
```

### Cleaning inactive accounts {#inactive_accounts}

Thanks to `lastlogin`{.interpreted-text role="ref"}, it is now possible
to monitor inactive accounts. An account is considered inactive if no
login has been recorded for the last 30 days (this value can be changed
through the admin panel).

A management command is available to disable or delete inactive
accounts. 

For example, you could setup a cron job to run it every night:

```txt
0 0 * * * <modoboa_site>/manage.py clean_inactive_accounts
#
# Or like this if you use a virtual environment:
# 0 0 * * * <virtualenv path/bin/python> <modoboa_site>/manage.py clean_inactive_accounts
```

The default behaviour is to disable accounts. You can delete them using the `--delete` option.

## DMARC reports

::: warning
A set of tools to use DMARC through Modoboa.

This feature is still in BETA stage, for now it only parses XML
aggregated reports and generate visual reports on a per-domain basis.
:::

### Installation

::: info
modoboa-installer can automatically set it up for you.
:::

Make sure to install the following additional system package according
to your distribution:

* Debian / Ubuntu: libmagic1
* CentOS: file-devel

### Integration with Postfix

A management command is provided to automatically parse DMARC aggregated
reports (rua) and feed the database. 

The execution of this command can be automated with the definition of a 
postfix service and a custom transport table.

First, declare a new service in `/etc/postfix/master.cf`:

```txt
dmarc-rua-parser unix  -       n       n       -       -       pipe
    flags= user=vmail:vmail argv=<path to python> <path to modoboa instance>/manage.py import_aggregated_report --pipe
```

Define a new transport table inside `/etc/postfix/main.cf`:

```txt
transport_maps =
    hash:/etc/postfix/dmarc_transport
    # other transport maps...
```

Create a file called `/etc/postfix/dmarc_transport` with the following content:

```txt
<email address your declared in your DNS record>  dmarc-rua-parser:
```

::: warning
You must not declare this email address as an identity (user account or
alias), else DMARC reports will be directed to your mailbox and won\'t
be parsed.
:::

Hash the file using the following command:

```shell
$ postmap /etc/postfix/dmarc_transport
```

Finally, reload postfix:

```shell
$ service postfix reload
```
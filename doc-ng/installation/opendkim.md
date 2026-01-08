# OpenDKIM

Modoboa can generate [DKIM](https://en.wikipedia.org/wiki/DomainKeys_Identified_Mail) keys
for the hosted domains but it won't sign or check messages.

To do that, you need a dedicated software like [OpenDKIM](http://opendkim.org/).

::: warning
The cron job in charge of creating DKIM keys must be run using the same
user than `OpenDKIM` (ie. opendkim in most cases).
:::

## Database

Since keys related information is stored in Modoboa's database, you
need to tell OpenDKIM how it can access it.

First, make sure to install the required additional packages on your
system (`libopendbx1-*` on debian based distributions or `opendbx-*` on
CentOS, the complete name depends on your database engine).

Then, insert the following SQL view into Modoboa\'s database:

::: code-group

```sql [PostgreSQL]
CREATE OR REPLACE VIEW dkim AS (
    SELECT id, name as domain_name, dkim_private_key_path AS private_key_path,
        dkim_key_selector AS selector
    FROM admin_domain WHERE enable_dkim
);
```

```sql [MySQL]
CREATE OR REPLACE VIEW dkim AS (
    SELECT id, name as domain_name, dkim_private_key_path AS private_key_path,
        dkim_key_selector AS selector
    FROM admin_domain WHERE enable_dkim=1
);
```
:::

## Configuration

You should find OpenDKIM\'s configuration file at `/etc/opendkim.conf`.

Add the following content to it:

``` txt
KeyTable		dsn:<driver>://<user>:<password>@<db host>/<db name>/table=dkim?keycol=id?datacol=domain_name,selector,private_key_path
SigningTable	dsn:<driver>://<user>:<password>@<db host>/<db name>/table=dkim?keycol=domain_name?datacol=id
Socket          inet:12345@localhost
```

Replace values between `<>` by yours. Accepted values for `driver` are
`pgsql` or `mysql`. Make sure the user you specify has read permission
on the view created previously.

If you run a debian based system, make sure to adjust the following
setting in the `/etc/default/opendkim` file:

``` txt
SOCKET=inet:12345@127.0.0.1
```

Eventually, `reload OpenDKIM`.

## Postfix integration

Add the following lines to the `/etc/postfix/main.cf` file:

``` txt{1,2}
smtpd_milters = inet:127.0.0.1:12345
non_smtpd_milters = inet:127.0.0.1:12345
milter_default_action = accept
milter_content_timeout = 30s
```

and `reload postfix`.
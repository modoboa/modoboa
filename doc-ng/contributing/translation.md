---
title: translation guide for modoboa
description: How to help to translate modoboa for your natural language
head:
  - - meta
    - name: 'keywords'
      content: 'modoboa, i18n, translation, transifex, makemessages, backend, frontend' 
---

# Translation

Modoboa needs you to translate the project ! Feel free to join the
translation team.

The project is using Transifex. To start with translation, you will need
to create an account and join 
[modoboa's team](https://app.transifex.com/tonio/modoboa/dashboard/)

## API

Modoboa API code relies on Django's translation system.

To update translation files after a change to the code, execute the following commands:

```shell
$ cd modoboa
$ django-admin makemessages -a
```

## Frontend

When editing the frontend, you may need to update localization files for
transifex to pick up your changes.

To do so, after finishing editing, go to the frontend directory and run
the following command:

```shell
$ yarn gettext:extract
```

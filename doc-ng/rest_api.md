---
title: REST API to control your Modoboa instance.
description: Guide to describe the use of the REST API to manage your modoboa instance
head:
  - - meta
    - name: 'keywords'
      content: 'modoboa, rest api, swagger, authorization, token' 
---

# REST API

To ease the integration with external sources (software or other), Modoboa provides a REST API.

Every installed instance comes with a ready-to-use API and a documentation.

**You will find them using the following url patterns:**

- New API+Docs: *https://\<hostname\>/api/schema-v2/swagger/*
- Old API: *http://\<hostname\>/api/v1/*

::: warning
You need to be logged in for the API docs to show.
:::

**Examples:**

* [Demo Instance](https://demo.modoboa.org/api/schema-v2/swagger/ "Demo Instance Swagger API")

documentation is available on the official demo.

Using this API requires an authentication and for now, only a token
based authentication is supported. To get a valid token, log-in to your
instance with a super administrator, go to `Settings > API` and
activate the API access. Press the Update button and wait until the page
is reloaded, the token will be displayed.

![image](/api_access_form.png){.align-center}

To make valid API calls, every requests you send must embed this token
within an Authorization HTTP header like this:

    Authorization: Token <YOUR_TOKEN>

and the content type of those requests must be `application/json`.
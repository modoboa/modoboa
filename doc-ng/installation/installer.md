---
title: Guide to install modoboa with the automatic installer
description: This guide describe how to install modoboa with the automatic installer
head:
  - - meta
    - name: 'keywords'
      content: 'modoboa, installation, webserver, nginx, apache, wsgi' 
---

# Automatic Installer

## Introduction

If you start from scratch and want to deploy a complete mail server,

you will love the [modoboa installer](https://github.com/modoboa/modoboa-installer)! 

It is the easiest and the quickest way to setup a fully functional server
(modoboa, postfix, dovecot, amavis and more) on one machine.

## How to start

::: warning
For now, only Debian based Linux distributions are supported.

We do our best to improve compatibility but if you use another `Linux` 
or a `UNIX` system, you will have to install Modoboa `manually <by_hand>`.
:::

To use it, just run the following commands in your terminal:

``` shell
$ git clone https://github.com/modoboa/modoboa-installer
$ cd modoboa-installer
$ sudo ./run.py <your domain>
```

::: warning
if you get this warning 

```console
'/usr/bin/env: 'python': No such file or directory', 
```

do make sure sure python is installed on your server. 

Sometimes python is installed but the installer can't detect it or which python version to run,
especially on a debian based system, check the `PATH` variable for the current user.

Then run this command first.

``` shell
$ sudo apt-get install python3-virtualenv python3-pip
```

:::

For the sake of simplicity, you can also install the `python-is-python3` package. 

It allows you to use `python` command and point to the python3 runtime.

Wait a few minutes and you're done 😎
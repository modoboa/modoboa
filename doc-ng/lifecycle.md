---
title: Modoboa Lifecycle
description: Modoboa version lifecycle
head:
  - - meta
    - name: 'keywords'
      content: 'modoboa, lifecycle, eol, lts, debian, ubuntu, python'
---

Modoboa's lifecycle is closely tied to the support calendar of the [Django](https://docs.djangoproject.com/en/6.0/faq/install/) framework's Long Term Support (LTS) releases. 

This approach guarantees a stable and secure production environment for the mail management solution.
Here is the complete summary of Modoboa's compatibility and lifecycle, structured around the supported versions of Python and Django.

## Current and Future Lifecycle

Modoboa's active development branch relies on the current Django LTS release to maximize the longevity of mail server installations.

![Django Release Roadmap](/django_release_roadmap.png "Django release Roadmap")

## Current Cycle: Modoboa 2.x

* Target Django Version: Django 5.2 LTS
* Supported Python Versions: [Python 3.10](https://www.python.org/downloads/), 3.11, 3.12, 3.13, 3.14
* Estimated End of Life (EOL): April 2028 (aligned with Django 5.2 LTS support)

## Future Cycle: Modoboa 3.0+ (Next LTS)

* Target Django Version: Django 6.2 LTS
* Supported Python Versions: Python 3.12 +
* Estimated End of Life (EOL): April 2030 (matching [Django 6.2 LTS end of life](https://www.djangoproject.com/download/6.2/roadmap/ "Django 6.2 roadmap"))

## Modoboa Lifecycle Strategy

The development team maintains Modoboa's architecture by strictly respecting the boundaries of its core technical stack:

* LTS Versions Priority: Modoboa gives priority to Django LTS releases. This provides mail administrators with predictable 3-year maintenance cycles without requiring major framework upgrades.
* Dropping Obsolete Python Versions: As soon as a Python release reaches its global end of life as declared by the Python Software Foundation, Modoboa drops support for it in its next minor or major update.
* Synchronized Extension Upgrades: The lifecycles of additional official building blocks (such as Webmail or Calendar) are tightly coupled with the core. They are released together to prevent API compatibility breaks during Django upgrades.


## Recommendations for Administrators

To guarantee the long-term maintainability and security of your Modoboa mail server:

* Always install Modoboa inside a Python virtual environment (virtualenv) to isolate its dependencies from the system's global packages.
* Use at least Python 3.12 for new installations to easily fulfill the system requirements of recent Modoboa releases.
* Keep track of new releases and security fixes by regularly visiting the [Modoboa Official Blog](https://modoboa.org/en/blog/) to plan your maintenance windows. 



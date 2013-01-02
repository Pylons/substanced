=============
Configuration
=============

While writing a Substance D application is very similar to writing a
Pyramid application, there are a few extra considerations to keep in
mind.

Scan and Include
================

When writing Pyramid applications, the Configurator supports
``config.include`` and ``config.scan`` Because of ordering
effects, do all your ``config.include`` calls before any of your
``config.scan`` calls.


=======================
Dumping Content to Disk
=======================

Substance D's object database stores native Python representations of
resources. This is easy enough to work with: you can run
``bin/pshell`` to get an interactive prompt, write longer ad-hoc
console scripts, or just put code into your application.

However, production sites usually want exportable representations of
important data stored in a long-term format. For this,
Substance D provides a dump facility for content types to be serialized
in a `YAML <http://yaml.org/>`_  representation on disk.


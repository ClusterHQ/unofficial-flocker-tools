#!/usr/bin/env python

"""
A prototype version of a CLI tool which shows off flocker's first class volumes
capabilities.

Key idea: make this especially useful in conjunction with the flocker docker
plugin.

For now, assume the existence of a user certificate as indicated by a
cluster.yml on this host which has a `users` key. Use the first user
certificate in that list.

* http://foutaise.org/code/texttable/

Idea for CLI:

$ flocker --help

$ flocker version
Client version: 1.0.0
Server version: 1.0.0

$ flocker node list
SERVER    ADDRESS    VOLUMES
0f72ae0c  1.2.3.4    3
6af074e4  1.2.3.5    2

$ flocker volume list [--deleted]
DATASET    SIZE    METADATA            STATUS       SERVER
1921edea   30GB    name=postgresql_7   pending      <none>
14f2fa0c   30GB    name=postgresql_8   attached     1.2.3.5
14f2fa0c   30GB    name=postgresql_8   unattached   <none>

$ flocker volume destroy name=badger
Marking volume c548725a to be destroyed.
"""


"""
Later ideas:

TODO: make it possible to see which containers are using which volumes via metadata updates.

$ flocker volume list
DATASET    SERVER   CONTAINERS      SIZE    METADATA
1921edea   1.2.3.4  pgsql7,pgsql9   30GB    name=postgresql_7
14f2fa0c   1.2.3.5  pgsql8          30GB    name=postgresql_8
b31a0311   <none>   <none>          30GB    name=nonmanifest

$ flocker volume destroy name=badger
Volume c548725a is currently in use. Please stop it first.

TODO: make metadata name be special/unique.

$ flocker volume create --size 30g name=badger
Volume "badger" already exists. Please choose another name.
"""

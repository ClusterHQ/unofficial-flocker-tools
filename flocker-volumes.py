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

$ ./flocker-volumes.py
Subcommands:
    version             show version informatioon

    list-nodes          show list of nodes in the configured cluster

    list                list flocker datasets
      --deleted          include deleted datasets

    create              create a flocker dataset
      --host 0f72ae0c    [-h] initial host for dataset to appear on
      --metadata name=hi [-m] set volume metadata
      --size 20G         [-s] set size in bytes (default), k, G, T

    destroy             mark a dataset to be deleted

    move                move a dataset from one primary to another

$ ./flocker-volumes.py version
Client version: 1.0.0
Server version: 1.0.0

$ ./flocker-volumes.py list-nodes
SERVER    ADDRESS    VOLUMES
0f72ae0c  1.2.3.4    3
6af074e4  1.2.3.5    2

$ ./flocker-volumes.py create -h 6af074e4 -m name=postgresql_8 -s 20G
14f2fa0c1a14f2fa0c14f2fa0c14f2fa0

$ ./flocker-volumes.py list [--deleted]
DATASET    SIZE    METADATA            STATUS       SERVER
14f2fa0c   20GB    name=postgresql_8   pending      6af074e4 (1.2.3.5)
1921edea   30GB    name=postgresql_7   attached     6af074e4 (1.2.3.5)
4ba2a30d   30GB    name=postgresql_8   unattached   <none>

$ ssh 1.2.3.5 docker run -d -v postgresql_8:/data/db --volume-driver=flocker --name=pgsql
383ab293ac7a7d533d83ab293c77d533d

[time passes...]

$ ssh 1.2.3.5 docker rm -f -v pgsql
383ab293ac7a7d533d83ab293c77d533d

$ ./flocker-volumes.py destroy 14f2fa0c
Marking volume 14f2fa0c to be destroyed.
"""

from twisted.python.usage import Options

class NodeList(Options):
    pass


"""
Later ideas:

TODO: make it possible to see which containers are using which volumes via metadata updates.

$ ./flocker-volumes.py list
DATASET    SERVER   CONTAINERS      SIZE    METADATA
1921edea   1.2.3.4  pgsql7,pgsql9   30GB    name=postgresql_7
14f2fa0c   1.2.3.5  pgsql8          30GB    name=postgresql_8
b31a0311   <none>   <none>          30GB    name=nonmanifest

$ ./flocker-volumes.py destroy name=badger
Volume c548725a is currently in use. Please stop it first.

TODO: make metadata name be special/unique.

$ ./flocker-volumes.py create --size 30g name=badger
Volume "badger" already exists. Please choose another name.
"""

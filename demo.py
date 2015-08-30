from __future__ import unicode_literals
import locale, sys, os
from dialog import Dialog
from twisted.python.filepath import FilePath

"""
A tool which aims to get people started with Flocker quickly, on OS X or Linux.
Teaches the user about what is about to happen, then writes out a cluster.yml
in a known specific directory in a hopefully-user-friendly way, then runs
flocker-install and flocker-config on the config file.

Expects to run inside a container which is started like this:

    $ docker run -ti -e PWD="$PWD" -v /:/host clusterhq/uft
"""

locale.setlocale(locale.LC_ALL, '')

HOST_PREFIX = "/host"

def host_path(path):
    return FilePath(HOST_PREFIX + "/" + path.path)

args = dict(width=0, height=0)

d = Dialog(dialog="dialog")
d.set_background_title("Experimental Flocker Installer - v0.4")
a = d.yesno("""Welcome to the Experimental Flocker Installer. This will help \
you install a Flocker cluster on some servers. You will:

* Create a local directory for the cluster you are configuring
* Spin up and configure some nodes
* Decide which storage backend to use and configure it

This process should take about 10-15 minutes.

Are you ready to begin?
""", title="Introduction", **args)
if a != d.OK:
    sys.exit(0)
else:
    pwd = FilePath(os.environ["PWD"])
    proposed = pwd.child("flocker-clusters")
    code, user_input = d.inputbox(
"""First, we need to create a directory on your local machine \
where you'll keep the configuration files and certificates for each of your \
clusters.

We assume that you started the installer in a location that's appropriate for \
this, so we propose creating a "flocker-clusters" sub-directory, if it doesn't \
already exist. If you want to change this default, do so now, otherwise \
proceed.

We'll create a subdirectory inside this directory for each of the clusters \
you create.
""", title="Local clusters directory", init=proposed.path, **args)
    if code != d.OK:
        sys.exit(0)
    else:
        clusters_path = FilePath(user_input)
        if host_path(clusters_path).exists():
            d.msgbox("The directory you chose already exists, which is fine.", **args)
        else:
            host_path(clusters_path).makedirs()
            d.msgbox("Created directory.", **args)

# TODO: list clusters in the directory, for each cluster, allow editing; list
# nodes and other configuration.


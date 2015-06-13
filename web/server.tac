# Copyright ClusterHQ Inc. See LICENSE file for details.

import flockerclient

from twisted.application import service, internet
from twisted.web import server

def getAdapter():
    root = flockerclient.get_root()
    site = server.Site(root)
    return site

application = service.Application("Insecure Flocker Client REST API")
adapterServer = internet.TCPServer(8088, getAdapter())
adapterServer.setServiceParent(application)

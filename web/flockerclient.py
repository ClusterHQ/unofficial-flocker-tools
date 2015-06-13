from txflocker.client import get_client as txflocker_get_client
from twisted.python.filepath import FilePath
from twisted.python import log
from twisted.web import resource, server
import os
import treq
import json

"""
Supported verb/url tuples:

    GET /v1/nodes

    GET /v1/datasets
    POST /v1/datasets

For debugging:

    GET /v1/version
    GET /v1/configuration/datasets
    GET /v1/state/datasets
"""

class BaseResource(resource.Resource):
    def __init__(self, *args, **kw):
        self.base_url = get_base_url()
        self.client = get_client()
        return resource.Resource.__init__(self, *args, **kw)

def simpleProxyFactory(proxy_path):
    """
    GET-only proxy factory
    """
    class ProxyResource(BaseResource):
        def __init__(self, *args, **kw):
            self.proxy_path = proxy_path
            return BaseResource.__init__(self, *args, **kw)
        def render_GET(self, request):
            d = self.client.get(self.base_url + self.proxy_path)
            d.addCallback(treq.json_content)
            def got_result(result):
                # proxy straight thru
                request.setHeader("content-type", "application/json")
                request.setHeader("access-control-allow-origin", "*")
                request.write(json.dumps(result))
                request.finish()
            d.addCallback(got_result)
            d.addErrback(log.err, "while trying to query backend")
            return server.NOT_DONE_YET
    return ProxyResource()

def get_root():
    state = resource.Resource()
    state.putChild("datasets", simpleProxyFactory("/state/datasets"))

    configuration = resource.Resource()
    configuration.putChild("datasets",
            simpleProxyFactory("/configuration/datasets"))

    v1 = resource.Resource()
    # passthru endpoints:
    v1.putChild("configuration", configuration)
    v1.putChild("state", state)
    v1.putChild("version", simpleProxyFactory("/version"))

    # top level synthesized endpoints:
    v1.putChild("nodes", simpleProxyFactory("/state/nodes"))

    v1.putChild("datasets", CombinedDatasets())

    root = resource.Resource()
    root.putChild("v1", v1)
    return root

def get_hostname():
    return os.environ["CONTROL_SERVICE"]

def get_user():
    return os.environ.get("USERNAME", "user")

def get_certificates_path():
    return FilePath(os.environ.get("CERTS_PATH", ".."))

def get_client():
    certificates_path = get_certificates_path()
    user_certificate_filename = "%s.crt" % (get_user(),)
    user_key_filename = "%s.key" % (get_user(),)
    return txflocker_get_client(
        certificates_path=certificates_path,
        user_certificate_filename=user_certificate_filename,
        user_key_filename=user_key_filename,
        target_hostname=get_hostname(),
    )

def get_base_url():
    return "https://%(hostname)s:4523/v1" % dict(
            hostname=get_hostname(),)

class CombinedDatasets(resource.Resource):
    # GET, POST
    pass

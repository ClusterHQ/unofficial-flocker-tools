from ..txflocker import client as txflocker_get_client
from twisted.python.filepath import FilePath
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

    GET /v1/configuration/datasets
    GET /v1/state/datasets
"""

def get_root():
    state = resource.Resource()
    state.putChild("datasets", StateDatasets())

    configuration = resource.Resource()
    configuration.putChild("datasets", ConfigurationDatasets())

    v1 = resource.Resource()
    # passthru endpoints:
    v1.putChild("configuration", configuration)
    v1.putChild("state", state)

    # top level synthesized endpoints:
    v1.putChild("nodes", StateNodes())
    v1.putChild("datasets", CombinedDatasets())

    root = resource.Resource()
    root.putChild("v1", v1)
    return root

class BaseResource(resource.Resource):
    def __init__(self, *args, **kw):
        self.base_url = get_base_url()
        self.client = get_client()
        return resource.Resource.__init__(*args, **kw)

def stupidProxyFactory(proxy_path):
    """
    GET-only proxy factory
    """
    class Proxy(BaseResource):
        def __init__(self, *args, **kw):
            self.proxy_path = proxy_path
            return BaseResource.__init__(*args, **kw)
        def render_GET(self, request):
            d = self.client.get(self.base_url + self.proxy_path)
            d.addCallback(treq.json_content)
            def got_result(result):
                # proxy straight thru
                request.setHeaders({"content-type": "application/json"})
                request.write(json.dumps(result))
                request.finish()
            d.addCallback(got_result)
            return server.NOT_DONE_YET
    return Proxy()

StateNodes = stupidProxyFactory("/state/nodes")
StateDatasets = stupidProxyFactory("/state/datasets")
ConfigurationDatasets = stupidProxyFactory("/configuration/datasets")

class CombinedDatasets(resource.Resource):
    # GET, POST
    pass

# utility functions for turning env vars into a treq object with tls
# context

def get_hostname():
    return os.environ["CONTROL_SERVICE"]

def get_user():
    return os.environ.get("USERNAME", "user")

def get_certificates_path():
    return os.environ.get("CERTS_PATH", ".")

def get_client():
    certificates_path = FilePath("..")
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

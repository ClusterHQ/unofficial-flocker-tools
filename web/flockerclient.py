from twisted.python.filepath import FilePath
from twisted.python import log
from twisted.web import resource, server
from twisted.web.static import File
from twisted.internet import defer
from txflocker.client import combined_state, parse_num, process_metadata
from txflocker.client import get_client as txflocker_get_client
import json
import os
import treq

"""
Supported verb/url tuples:

    GET /v1/nodes
    GET /v1/nodes/:uuid

    GET /v1/datasets
    GET /v1/datasets/:uuid

    POST /v1/datasets
    PUT /v1/datasets/:uuid (maps to POST)

    DELETE /v1/datasets/:uuid TODO

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

class ChildProxyResource(BaseResource):
    def __init__(self, child_id, proxy_path, *args, **kw):
        self.child_id = child_id
        self.proxy_path = proxy_path
        return BaseResource.__init__(self, *args, **kw)

    def render_GET(self, request):
        d = self.client.get(self.base_url + self.proxy_path)
        d.addCallback(treq.json_content)
        def got_result(results):
            request.setHeader("content-type", "application/json")
            request.setHeader("access-control-allow-origin", "*")
            for result in results:
                if result["uuid"] == self.child_id:
                    request.write(json.dumps(result))
                    request.finish()
                    return
            request.setResponseCode(400)
            request.write(json.dumps(dict(error="unable to find child %s" %
                (self.child_id,))))
        d.addCallback(got_result)
        def handle_failure(failure):
            request.setResponseCode(400)
            request.setHeader("content-type", "application/json")
            request.setHeader("access-control-allow-origin", "*")
            request.write(json.dumps(dict(error=str(failure))))
            request.finish()
            return failure
        d.addErrback(handle_failure)
        d.addErrback(log.err, "while trying to query backend" + self.base_url +
                self.proxy_path + "/" + self.child_id)
        return server.NOT_DONE_YET

def simpleProxyFactory(proxy_path):
    """
    GET and POST proxy factory (POST assumes it returns JSON too).
    """
    class ProxyResource(BaseResource):
        def __init__(self, *args, **kw):
            self.proxy_path = proxy_path
            return BaseResource.__init__(self, *args, **kw)

        def getChild(self, path, request):
            fragments = request.uri.split("/")
            return ChildProxyResource(child_id=fragments.pop().encode("ascii"),
                    proxy_path=self.proxy_path)

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
            def handle_failure(failure):
                request.setResponseCode(400)
                request.setHeader("content-type", "application/json")
                request.setHeader("access-control-allow-origin", "*")
                request.write(json.dumps(dict(error=str(failure))))
                request.finish()
                return failure
            d.addErrback(handle_failure)
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
    root.putChild("client", File("."))
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

class DatasetResource(resource.Resource):
    def __init__(self, dataset_id, *args, **kw):
        self.dataset_id = dataset_id
        return resource.Resource.__init__(self, *args, **kw)

    def render_GET(self, request):
        d = combined_state(get_client(), get_base_url(), deleted=False)
        def got_state(results):
            request.setHeader("content-type", "application/json")
            request.setHeader("access-control-allow-origin", "*")
            for result in results:
                if result["dataset_id"] == self.dataset_id:
                    request.write(json.dumps(result))
                    request.finish()
                    return
            request.setResponseCode(400)
            request.write(json.dumps(dict(
                error="unable to find %s" % (self.dataset_id,))))
            request.finish()
        d.addCallback(got_state)
        d.addErrback(log.err, "while trying to GET child dataset")
        return server.NOT_DONE_YET

    def render_PUT(self, request):
        return self.render_POST(request)

    def render_POST(self, request):
        request_raw = json.loads(request.content.read())
        client = get_client()
        if "primary" not in request_raw:
            d = defer.fail(Exception("must specify primary"))
        else:
            d = client.post(get_base_url() + "/configuration/datasets/%s" %
                    (self.dataset_id,), json.dumps({"primary": request_raw["primary"]}),
                    headers={"content-type": "application/json"})
            d.addCallback(treq.json_content)
        def got_result(result):
            request.setHeader("content-type", "application/json")
            request.setHeader("access-control-allow-origin", "*")
            request.write(json.dumps(dict(result="success")))
            request.finish()
        d.addCallback(got_result)
        def handle_failure(failure):
            request.setResponseCode(400)
            request.setHeader("content-type", "application/json")
            request.setHeader("access-control-allow-origin", "*")
            request.write(json.dumps(dict(error=str(failure))))
            request.finish()
            return failure
        d.addErrback(handle_failure)
        d.addErrback(log.err, "while trying to POST combined state")
        return server.NOT_DONE_YET

class CombinedDatasets(resource.Resource):
    def getChild(self, path, request):
        fragments = request.uri.split("/")
        return DatasetResource(dataset_id=fragments.pop().encode("ascii"))
    def render_GET(self, request):
        d = combined_state(get_client(), get_base_url(), deleted=True)
        def got_state(result):
            request.setHeader("content-type", "application/json")
            request.setHeader("access-control-allow-origin", "*")
            request.write(json.dumps(result))
            request.finish()
        d.addCallback(got_state)
        d.addErrback(log.err, "while trying to GET combined state")
        return server.NOT_DONE_YET
    def render_POST(self, request):
        request_raw = json.loads(request.content.read())
        try:
            if "meta" in request_raw:
                request_raw["metadata"] = process_metadata(request_raw.pop("meta"))
            if "size" in request_raw:
                request_raw["maximum_size"] = parse_num(request_raw.pop("size"))
        except Exception, e:
            request.setHeader("content-type", "application/json")
            request.setHeader("access-control-allow-origin", "*")
            request.setResponseCode(400)
            return json.dumps(dict(error=str(e)))
        client = get_client()
        d = client.post(get_base_url() + "/configuration/datasets",
                json.dumps(request_raw), headers={
                    "content-type": "application/json"})
        d.addCallback(treq.json_content)
        def got_result(result):
            request.setHeader("content-type", "application/json")
            request.setHeader("access-control-allow-origin", "*")
            request.write(json.dumps(result))
            request.finish()
        d.addCallback(got_result)
        def handle_failure(failure):
            request.setResponseCode(400)
            request.setHeader("content-type", "application/json")
            request.setHeader("access-control-allow-origin", "*")
            request.write(json.dumps(dict(error=str(failure))))
            request.finish()
            return failure
        d.addErrback(handle_failure)
        d.addErrback(log.err, "while trying to POST combined state")
        return server.NOT_DONE_YET

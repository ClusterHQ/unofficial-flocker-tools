"""
A collection of utilities for using the flocker REST API.
"""

from treq.client import HTTPClient
from OpenSSL import SSL

from twisted.internet import reactor
from twisted.internet import ssl as twisted_ssl
from twisted.internet.ssl import optionsForClientTLS
from twisted.python.filepath import FilePath
from twisted.web.client import Agent

import yaml

import httplib
import os
import ssl
import tempfile


def get_client(reactor=reactor, certificates_path=FilePath("/etc/flocker"),
        user_certificate_filename="node.crt", user_key_filename="node.key",
        cluster_certificate_filename="cluster.crt", target_hostname=None):
    """
    Create a ``treq``-API object that implements the REST API TLS
    authentication.

    That is, validating the control service as well as presenting a
    certificate to the control service for authentication.

    :param reactor: The reactor to use.
    :param FilePath certificates_path: Directory where certificates and
        private key can be found.

    :return: ``treq`` compatible object.
    """
    if target_hostname is None:
        config = certificates_path.child("agent.yml")
        if config.exists():
            agent_config = yaml.load(config.open())
            target_hostname = agent_config["control-service"]["hostname"]

    user_crt = certificates_path.child(user_certificate_filename)
    user_key = certificates_path.child(user_key_filename)
    cluster_crt = certificates_path.child(cluster_certificate_filename)

    if (user_crt.exists() and user_key.exists() and cluster_crt.exists()
            and target_hostname is not None):
        # we are installed on a flocker node with a certificate, try to reuse
        # it for auth against the control service
        #cert_data = cluster_crt.getContent()
        #auth_data = user_key.getContent() + user_crt.getContent()

        #authority = ssl.Certificate.loadPEM(cert_data)
        #client_certificate = ssl.PrivateCertificate.loadPEM(auth_data)

        class CtxFactory(twisted_ssl.ClientContextFactory):
            def getContext(self, hostname, port):
                self.method = SSL.SSLv23_METHOD
                ctx = ssl.ClientContextFactory.getContext(self)
                ctx.use_certificate_file(user_crt.path)
                ctx.use_privatekey_file(user_key.path)
                ctx.load_verify_locations(cluster_crt.path)
                def verifyCallback(*args):
                    print args
                    import pdb; pdb.set_trace()
                    return True
                ctx.set_verify(
                    SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT,
                    verifyCallback
                    )
                return ctx

        class FudgeFactory(twisted_ssl.ClientContextFactory):
            def getContext(self, hostname, port):
                # We must create a certificate chain and then pass that into
                # the SSL system.
                self.method = SSL.SSLv23_METHOD
                certtemp = tempfile.NamedTemporaryFile()
                TEMP_CERT_CA_FILE = certtemp.name
                os.chmod(TEMP_CERT_CA_FILE, 0600)
                certtemp.write(open(user_crt.path).read())
                certtemp.write("\n")
                certtemp.write(open(cluster_crt.path).read())
                certtemp.seek(0)
                ctx = twisted_ssl.ClientContextFactory.getContext(self)
                #ctx = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
                #ctx.load_cert_chain(TEMP_CERT_CA_FILE, user_key.path)
                # in pyopenssl, this is translated to:
                ctx.use_certificate_file(TEMP_CERT_CA_FILE)
                ctx.use_privatekey_file(user_key.path)
                return ctx
        return HTTPClient(Agent(reactor, contextFactory=FudgeFactory()))
    else:
        raise Exception("Not enough information to construct TLS context: "
                "user_crt: %s, cluster_crt: %s, user_key: %s, target_hostname: %s" % (
                    user_crt, cluster_crt, user_key, target_hostname))

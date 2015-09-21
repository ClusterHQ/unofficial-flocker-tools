import subprocess
from pipes import quote
import yaml
import os
import time
from contextlib import closing
from socket import socket
from twisted.internet import reactor
from twisted.internet.defer import maybeDeferred
from twisted.internet.task import deferLater
from twisted.internet.utils import _callProtocolWithDeferred
from twisted.internet import protocol
from io import BytesIO as StringIO
from twisted.python import failure

class SensibleProcessProtocol(protocol.ProcessProtocol):
    def __init__(self, deferred):
        self.deferred = deferred
        self.outBuf = StringIO()
        self.outReceived = self.outBuf.write
        self.errReceived = self.outBuf.write

    def processEnded(self, reason):
        out = self.outBuf.getvalue()
        e = reason.value
        code = e.exitCode
        if e.signal:
            self.deferred.errback(
                Exception("Process exited on signal %s: %s" % (e.signal, out)))
        elif code != 0:
            self.deferred.errback(
                Exception("Process exited with error code %s: %s" % (code, out)))
        else:
            self.deferred.callback(out)

def getSensibleProcessOutput(executable, args=(), env={}, path=None,
                             reactor=None):
    """
    Do what you would expect getProcessOutput to do:
    * if process emits stderr, capture it along with stdout
    * if process ends with exit code != 0 or signal, errback with combined process output
    * otherwise, callback with combined process output
    """
    return _callProtocolWithDeferred(SensibleProcessProtocol, executable, args, env, path,
                                     reactor)

def append_to_install_log(s):
    fp = open('install-log.txt', 'a')
    fp.write(str(int(time.time())) + ", " + s + "\n")
    fp.close()

def format_log_args(args):
    return " ".join([str(a) for a in args])

def log(*args):
    print format_log_args(args)
    append_to_install_log(format_log_args(args))

def verbose_log(*args):
    append_to_install_log(format_log_args(args))

def verbose_log_callback(result, message):
    verbose_log(message, result)
    return result

def verify_socket(host, port, timeout=120, connect_timeout=5):
    """
    Wait until the destionation can be connected to.

    :param bytes host: Host to connect to.
    :param int port: Port to connect to.

    :return Deferred: Firing when connection is possible.
    """
    def can_connect():
        with closing(socket()) as s:
            s.settimeout(connect_timeout)
            conn = s.connect_ex((host, port))
            return conn == 0

    log("Attempting to connect to %s:%s..." % (host, port))
    dl = loop_until(can_connect, timeout=timeout)
    then = time.time()
    def success(result, ip, port):
        log("Connected to %s:%s after %.2f seconds!" % (ip, port, time.time() - then))
    def failure(result, ip, port):
        log("Failed to connect to %s:%s after %.2f seconds :(" % (ip, port, time.time() - then))
    dl.addCallback(success, ip=host, port=port)
    dl.addErrback(failure, ip=host, port=port)
    return dl


class TimeoutError(Exception):
    pass


def loop_until(predicate, timeout=None):
    """Call predicate every 0.1 seconds, until it returns something ``Truthy``.

    :param predicate: Callable returning termination condition.
    :type predicate: 0-argument callable returning a Deferred.

    :return: A ``Deferred`` firing with the first ``Truthy`` response from
        ``predicate``.
    """
    d = maybeDeferred(predicate)
    then = time.time()
    def loop(result):
        if timeout and time.time() - then > timeout:
            raise TimeoutError()
        if not result:
            d = deferLater(reactor, 0.1, predicate)
            d.addCallback(loop)
            return d
        return result
    d.addCallback(loop)
    return d


class Configurator(object):
    def __init__(self, configFile):
        self.config = yaml.load(open(configFile))
        # set some defaults
        self.config["private_key_path"] = self.config.get("private_key_path", "~/.ssh/id_rsa")
        if "CONTAINERIZED" in os.environ:
            self.config["private_key_path"] = "/host" + self.config["private_key_path"]
        self.config["remote_server_username"] = self.config.get("remote_server_username", "root")

    def runSSH(self, ip, command, username=None):
        command = 'ssh -o LogLevel=error -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i %s %s@%s %s' % (self.config["private_key_path"],
                username if username is not None else self.config["remote_server_username"],
                ip, " ".join(map(quote, ["bash", "-c", "echo; " + command])))
        verbose_log("runSSH:", command)
        result = subprocess.check_output(command, shell=True)
        verbose_log("runSSH result of", command, " - ", result)
        return result

    def runSSHAsync(self, ip, command, username=None):
        """
        Use Twisted APIs, assuming a reactor is running, to return a deferred
        which fires with the result.
        """
        executable = "/usr/bin/ssh"
        command = ['-o', 'LogLevel=error', '-o', 'UserKnownHostsFile=/dev/null', '-o',
                   'StrictHostKeyChecking=no', '-i',
                   self.config["private_key_path"], "%s@%s" % (
                       username if username is not None else self.config["remote_server_username"], ip),
                   " ".join(map(quote, ["bash", "-c", "echo; " + command]))]
        verbose_log("runSSHAsync:", command)
        d = getSensibleProcessOutput(executable, command)
        d.addBoth(verbose_log_callback, message="runSSHAsync result of %s - " % (command,))
        return d

    def runSSHRaw(self, ip, command, username=None):
        command = 'ssh -o LogLevel=error -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i %s %s@%s %s' % (self.config["private_key_path"],
                username if username is not None else self.config["remote_server_username"],
                ip, command)
        verbose_log("runSSHRaw:", command)
        result = subprocess.check_output(command, shell=True)
        verbose_log("runSSHRaw result of", command, " - ", result)
        return result

    def run(self, command):
        verbose_log("run:", command)
        result = subprocess.check_output(command, shell=True)
        verbose_log("run result of", command, " - ", result)
        return result

    def scp(self, local_path, external_ip, remote_path,
            private_key_path=None, remote_server_username=None, async=False):
        if private_key_path is not None:
            private_key_path = self.config["private_key_path"]
        if remote_server_username is not None:
            remote_server_username = self.config["remote_server_username"]
        scp = ("scp -o LogLevel=error -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i %(private_key_path)s %(local_path)s "
               "%(remote_server_username)s@%(external_ip)s:%(remote_path)s") % dict(
                    private_key_path=self.config["private_key_path"],
                    remote_server_username=self.config["remote_server_username"],
                    external_ip=external_ip, remote_path=remote_path,
                    local_path=local_path)
        if async:
            verbose_log("scp async:", scp)
            d = getSensibleProcessOutput("/bin/bash", ["-c", scp])
            d.addBoth(verbose_log_callback, message="scp async result of %s - " % (scp,))
            return d
        else:
            verbose_log("scp sync:", scp)
            result = subprocess.check_output(scp, shell=True)
            verbose_log("scp sync result of", scp, " - ", result)
            return result

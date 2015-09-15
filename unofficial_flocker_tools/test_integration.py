# Copyright ClusterHQ Inc. See LICENSE file for details.

"""
Test supported configurations.
"""

from twisted.trial.unittest import TestCase
import os
from pipes import quote as shell_quote
from subprocess import PIPE, Popen
from twisted.python.filepath import FilePath
import yaml

KEY = FilePath(os.path.expanduser("~") + "/cloud-keys/key.pem")

class UnofficialFlockerInstallerTests(TestCase):
    """
    Complete spin-up tests.
    """
    # Slow builds because we're provisioning VMs.
    timeout = 60 * 60

    def _run_integration_test(self, configuration):
        test_dir = FilePath(self.mktemp())
        test_dir.makedirs()
        os.system("""cd %(testdir)s && \
            docker run -v $PWD:/config -v /var/run/docker.sock:/var/run/docker.sock ubuntu:14.04 \
                "apt-get install curl && \
                 curl -sSL https://get.flocker.io/ | sh && \
                 cd /config && \
                 uft-flocker-get-nodes --%(configuration)s && \
                 uft-flocker-install cluster.yml && \
                 uft-flocker-config cluster.yml && \
                 uft-flocker-plugin-install cluster.yml"
        """ % dict(testdir=test_dir.path, configuration=configuration))
        cluster_config = yaml.load(test_dir.child("config.yml").open())
        node1 = cluster_config['agent_nodes'][0]
        node2 = cluster_config['agent_nodes'][1]
        self.assertNotEqual(node1, node2)
        node1public = node1['public']
        node2public = node2['public']
        run(node1public, """
            docker run -v foo:/data --volume-driver=flocker busybox sh -c "echo hello > /data/foo"
        """)
        output = run(node2public, """
            docker run -v foo:/data --volume-driver=flocker busybox cat /data/foo
        """)
        self.assertEqual(output, "hello")
        os.system("""cd %(testdir)s && \
            docker run -v $PWD:/config -v /var/run/docker.sock:/var/run/docker.sock ubuntu:14.04 \
                "apt-get install curl && \
                 curl -sSL https://get.flocker.io/ | sh && \
                 cd /config && \
                 uft-flocker-volumes destroy --dataset=$(uft-flocker-volumes list | awk -F '-' '{print $0}) && \
                 while [ $(uft-flocker-volumes list |wc -l) != "1" ]; do echo waiting for volumes to be deleted; sleep 1; done"
        """ % dict(testdir=test_dir.path, configuration=configuration))

    def test_ubuntu_aws(self):
        return self._run_integration_test("ubuntu-aws")


def run(node, command, input=""):
    """
    Synchronously run a command (list of bytes) on a node's address (bytes)
    with optional input (bytes).
    """
    print "Running", command, "on", node
    result = run_SSH(22, "root", node, command, input, key=KEY)
    print "Output from", node + ":", result, "(%s)" % (command,)
    return result


def run_SSH(port, user, node, command, input, key=None,
            background=False):
    """
    Run a command via SSH.

    :param int port: Port to connect to.
    :param bytes user: User to run the command as.
    :param bytes node: Node to run command on.
    :param command: Command to run.
    :type command: ``list`` of ``bytes``.
    :param bytes input: Input to send to command.
    :param FilePath key: If not None, the path to a private key to use.
    :param background: If ``True``, don't block waiting for SSH process to
         end or read its stdout. I.e. it will run "in the background".
         Also ensures remote process has pseudo-tty so killing the local SSH
         process will kill the remote one.

    :return: stdout as ``bytes`` if ``background`` is false, otherwise
        return the ``subprocess.Process`` object.
    """
    quotedCommand = ' '.join(map(shell_quote, command))
    command = [
        b'ssh',
        b'-p', b'%d' % (port,),
        b'-o', b'StrictHostKeyChecking=no',
        b'-o', b'UserKnownHostsFile=/dev/null',
        ]

    if key is not None:
        command.extend([
            b"-i",
            key.path])

    if background:
        # Force pseudo-tty so that remote process exists when the ssh
        # client does:
        command.extend([b"-t", b"-t"])

    command.extend([
        b'@'.join([user, node]),
        quotedCommand
    ])
    if background:
        process = Popen(command, stdin=PIPE)
        process.stdin.write(input)
        return process
    else:
        process = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE)

    result = process.communicate(input)
    if process.returncode != 0:
        raise Exception('Command Failed', command, process.returncode, result)

    return result[0]

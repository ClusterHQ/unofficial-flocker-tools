# Copyright ClusterHQ Inc. See LICENSE file for details.

"""
Test supported configurations of the installer.

To run these tests, you must place a `terraform.tfvars.json` file in your home
directory thusly:

luke@tiny:~$ cat ~/terraform.tfvars.json
{"aws_access_key": "XXX",
 "aws_secret_key": "YYY",
 "aws_region": "us-west-1",
 "aws_availability_zone": "us-west-1b",
 "aws_key_name": "luke2",
 "private_key_path": "/Users/luke/Downloads/luke2.pem"}
"""

from twisted.trial.unittest import TestCase
import os
from subprocess import check_output
from twisted.python.filepath import FilePath
import yaml, json

SECRETS_FILE = FilePath(os.path.expanduser("~") + "/terraform.tfvars.json")
SECRETS = json.load(SECRETS_FILE.open())
KEY = FilePath(SECRETS["private_key_path"])
GET_FLOCKER = "https://get-dev.flocker.io/" # XXX remove "-dev" before merging to master
#UFT = "uft-"
UFT = ""

class UnofficialFlockerInstallerTests(TestCase):
    """
    Complete spin-up tests.
    """
    # Slow builds because we're provisioning VMs.
    timeout = 60 * 60

    def _run_integration_test(self, configuration):
        test_dir = FilePath(self.mktemp())
        test_dir.makedirs()
        v = dict(testdir=test_dir.path, get_flocker=GET_FLOCKER,
                 configuration=configuration, uft=UFT)
        cleaned_up = False
        try:
            os.system("""curl -sSL %(get_flocker)s | sh && \
                         cd %(testdir)s && \
                         %(uft)sflocker-sample-files""" % v)
            SECRETS_FILE.copyTo(test_dir.child("terraform").child("terraform.tfvars.json"))
            os.system("""cd %(testdir)s && \
                         %(uft)sflocker-get-nodes --%(configuration)s && \
                         %(uft)sflocker-install cluster.yml && \
                         %(uft)sflocker-config cluster.yml && \
                         %(uft)sflocker-plugin-install cluster.yml && \
                         echo "sleeping 10 seconds to let cluster settle..." && \
                         sleep 10""" % v)
            cluster_config = yaml.load(test_dir.child("cluster.yml").open())
            node1 = cluster_config['agent_nodes'][0]
            node2 = cluster_config['agent_nodes'][1]
            self.assertNotEqual(node1, node2)
            node1public = node1['public']
            node2public = node2['public']
            print runSSHRaw(node1public,
                'docker run -v foo:/data --volume-driver=flocker busybox '
                'sh -c \\"echo hello \\> /data/foo\\"')
            output = runSSHRaw(node2public,
                'docker run -v foo:/data --volume-driver=flocker busybox '
                'cat /data/foo')
            self.assertTrue(output.strip().endswith("hello"))
            result = os.system("""cd %(testdir)s && \
%(uft)sflocker-volumes destroy --dataset=$(%(uft)sflocker-volumes list|tail -n 2 |head -n 1|awk -F ' ' '{print $1}') && \
while [ $(%(uft)sflocker-volumes list |wc -l) != "2" ]; do echo waiting for volumes to be deleted; sleep 1; done && \
FORCE_DESTROY=yes %(uft)sflocker-destroy-nodes""" % v)
            if result == 0:
                cleaned_up = True
        finally:
            if not cleaned_up:
                os.system("""cd %(testdir)s && \
                             FORCE_DESTROY= %(uft)sflocker-destroy-nodes""" % v)

    def test_ubuntu_aws(self):
        return self._run_integration_test("ubuntu-aws")

def runSSHRaw(ip, command, username="root"):
    command = 'ssh -o LogLevel=error -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i %s %s@%s %s' % (
            KEY.path, username, ip, command)
    return check_output(command, shell=True)

#!/usr/bin/env python
import yaml, os
cluster = yaml.load(open("cluster.yml"))
# assumes control service is on an agent node
servers = [
    "ssh -i %(private_key_path)s root@%(ip)s" % dict(
        ip=node["public"],
        private_key_path=cluster["private_key_path"])
    for node in cluster["agent_nodes"]]
name = "flocker-" + cluster.get("cluster_name")
tmuxinator_config = {
        "name": name,
        "windows": [{"servers": {"layout": "even-vertical", "panes": servers}}],
        }
path = os.path.expanduser("~") + "/.tmuxinator/" + name + ".yml"
print "writing config to " + path
yaml.dump(tmuxinator_config, open(path, "w"))
print "run it with 'tmuxinator start %s'" % (name,)

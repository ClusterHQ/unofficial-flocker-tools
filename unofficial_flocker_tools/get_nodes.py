#!/usr/bin/env python

import os
from twisted.python.filepath import FilePath
from twisted.python.usage import UsageError

def main():
    terraform = FilePath("terraform")
    if not terraform.exists():
        print "Please run uft-flocker-sample-files in the current directory first."
        os._exit(1)
    os.system("cd terraform && terraform apply")
    cluster_yml = terraform.child("cluster.yml")
    if cluster_yml.exists():
        cluster_yml.moveTo(FilePath(".").child("cluster.yml"))
    else:
        raise UsageError("Infrastructure failed to provision: cluster.yml was not created")

if __name__ == "__main__":
    main()


#!/usr/bin/env python

import os
from twisted.python.filepath import FilePath

def main():
    terraform = FilePath("terraform")
    if not terraform.exists():
        print "Please run uft-flocker-sample-files in the current directory first."
        os._exit(1)
    os.system("cd terraform && terraform apply")
    cluster_yml = terraform.child("cluster.yml")
    if cluster_yml.exists():
        cluster_yml.moveTo(FilePath(".").child("cluster.yml"))

if __name__ == "__main__":
    main()


#!/usr/bin/env python

import os
from twisted.python.filepath import FilePath

def main(force=False):
    terraform_templates = FilePath("terraform")
    if not terraform_templates.exists():
        print "Please run uft-flocker-sample-files in the current directory first."
        os._exit(1)
    os.system("cd terraform && terraform destroy"
            + (" -force" if force or os.environ.get("FORCE_DESTROY") else ""))
    pass

if __name__ == "__main__":
    main()

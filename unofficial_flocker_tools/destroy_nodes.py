#!/usr/bin/env python

import os
from twisted.python.filepath import FilePath

def main():
    terraform_templates = FilePath("terraform")
    if not terraform_templates.exists():
        print "Please run uft-flocker-sample-files in the current directory first."
        os._exit(1)
    os.system("cd terraform && terraform destroy"
            + (" -force" if "FORCE_DESTROY" in os.environ else ""))
    pass

if __name__ == "__main__":
    main()

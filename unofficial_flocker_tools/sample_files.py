import os
from pkg_resources import resource_filename

def main():
    target_dir = "terraform"
    terraform_templates = resource_filename("unofficial_flocker_tools", "terraform_templates")
    os.system("mkdir -p %(target_dir)s && cp %(terraform_templates)s/* %(target_dir)s/"
            # XXX escaping
            % dict(terraform_templates=terraform_templates, target_dir=target_dir))
    print "Copied sample files into current directory."

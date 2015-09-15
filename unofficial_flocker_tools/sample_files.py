import shutil
from pkg_resources import resource_filename

def main():
    print "Copying the following files to the current working directory:"

    for backend in ["ebs", "openstack", "zfs"]:
        filename = "cluster.yml.%s.sample" % (backend,)
        resource = resource_filename("unofficial_flocker_tools", "samples/" + filename)
        shutil.copyfile(resource, filename)
        print filename

    terraform_templates = resource_filename("unofficial_flocker_tools", "terraform_templates")
    print terraform_templates
    shutil.copytree(terraform_templates, ".")

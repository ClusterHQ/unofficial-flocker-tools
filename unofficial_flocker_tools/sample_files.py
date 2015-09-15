import shutil
from pkg_resources import resource_filename

def main():
    print "Copying the following files to the current working directory:"

    for backend in ["ebs", "openstack", "zfs"]:
        filename = "cluster.yml.%s.sample" % (backend,)
        resource = resource_filename("unofficial_flocker_tools", "samples/" + filename)
        shutil.copyfile(resource, filename)
        print filename

    target_dir = "terraform_templates"
    terraform_templates = resource_filename("unofficial_flocker_tools", target_dir)
    print target_dir
    shutil.copytree(terraform_templates, target_dir)

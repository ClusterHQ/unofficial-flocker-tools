import shutil, os
from pkg_resources import resource_filename

def main():
    print "Copying the following files to the current working directory:"

    for backend in ["ebs", "openstack", "zfs"]:
        filename = "cluster.yml.%s.sample" % (backend,)
        resource = resource_filename("unofficial_flocker_tools", "samples/" + filename)
        shutil.copyfile(resource, filename)
        print filename

    target_dir = "terraform"
    terraform_templates = resource_filename("unofficial_flocker_tools", "terraform_templates")
    print target_dir
    print "copying", terraform_templates, "=>", os.getcwd(), "./" + target_dir
    os.system("mkdir -p %(target_dir)s && cp %(terraform_templates)s/* %(target_dir)s/"
            % dict(terraform_templates=terraform_templates, target_dir=target_dir))

from fabric.api import task, env, local
from pipes import quote as shellQuote
import getpass
import os

env.user = getpass.getuser()

vagrant_plugins = {'ansible': '0.2.0',
                   'vagrant-hostmanager': '1.5.0',
                   'vagrant-triggers': '0.4.3',
                   'vagrant-hostsupdater': '0.0.11'}

galaxy_roles = ['Azulinho.azulinho-google-dns',
                'Azulinho.azulinho-ssh-keys',
                'aeriscloud.docker',
                'mbasanta.pip']

INSTALLED_VAGRANT_PLUGINS = local('vagrant plugin list', capture=True)


@task
def setup():
    install_vagrant_plugins(vagrant_plugins)
    install_ansible()
    install_galaxy_roles(galaxy_roles)
    vagrant_up()
    vagrant_provision()


def cmd(*args):
    return ' '.join(map(shellQuote, args))


def install_vagrant_plugins(vagrant_plugins):
    for plugin, version in vagrant_plugins.items():
        if is_vagrant_plugin_installed(plugin) is False:
            local('vagrant plugin install %s --plugin-version %s'
                  % (plugin, version),
                  capture=True)


def is_vagrant_plugin_installed(vagrant_plugin):
    if vagrant_plugin in INSTALLED_VAGRANT_PLUGINS:
        return True
    else:
        return False


def install_galaxy_roles(galaxy_roles):
    for galaxy_role in galaxy_roles:
        # only install if the role is missing
        if not os.path.isdir('roles/' + galaxy_role):
            local(
                cmd('ansible-galaxy',  'install', galaxy_role,
                    '-p', './roles', '--force'))


def install_ansible():
    if is_ansible_installed is False:
        local('pip install ansible', capture=True)


def is_ansible_installed():
    output = local('pip list', capture=True)
    if 'ansible' in output:
        return True
    else:
        return False


@task
def vagrant_up():
    local('vagrant up --no-provision')
    vagrant_provision()


@task
def vagrant_provision():
    local('vagrant provision')


@task
def vagrant_destroy():
    local('vagrant destroy -f')

@task
def vagrant_reload():
    vagrant_destroy()
    vagrant_up()


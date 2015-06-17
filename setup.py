from setuptools import setup

setup(
    name='Unofficial Flocker Tools',
    packages=[
        'unofficial_flocker_tools',
        'unofficial_flocker_tools.txflocker'
    ],
    entry_points={
        'console_scripts': [
            'flocker-deploy= unofficial_flocker_tools.deploy:main',
            'flocker-install= unofficial_flocker_tools.install:main',
            'flocker-plugin-install= unofficial_flocker_tools.plugin:main',
            'flocker-volumes = unofficial_flocker_tools.flocker_volumes:_main',
            'flocker-tutorial= unofficial_flocker_tools.tutorial:main',
        ],
    },
    version='0.1',
    description='Unofficial installer and utilities for Flocker.',
    author='Luke Marsden',
    author_email='luke@clusterhq.com',
    url='https://github.com/ClusterHQ/unofficial-flocker-tools',
    install_requires=[
        'PyYAML>=3',
        'Twisted>=14',
        'treq>=14',
    ],
)

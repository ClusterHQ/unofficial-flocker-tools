from setuptools import setup

setup(
    name='Unofficial Flocker Tools',
    packages=[
        'unofficial_flocker_tools',
        'unofficial_flocker_tools.txflocker'
    ],
    entry_points={
        'console_scripts': [
            'flocker-config= unofficial_flocker_tools.deploy:main',
            'flocker-install= unofficial_flocker_tools.install:main',
            'flocker-plugin-install= unofficial_flocker_tools.plugin:main',
            'flocker-tutorial= unofficial_flocker_tools.tutorial:main',
            'flocker-volumes = unofficial_flocker_tools.flocker_volumes:_main',
        ],
    },
    version='0.1',
    description='Unofficial tools to make installing and using Flocker easier and more fun.',
    author='Luke Marsden',
    author_email='luke@clusterhq.com',
    url='https://github.com/ClusterHQ/unofficial-flocker-tools',
    install_requires=[
        'PyYAML>=3',
        'Twisted>=14',
        'treq>=14',
    ],
)

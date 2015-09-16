from setuptools import setup

setup(
    name="UnofficialFlockerTools",
    packages=[
        "unofficial_flocker_tools",
        "unofficial_flocker_tools.txflocker",
    ],
    package_data={
        "unofficial_flocker_tools": ["samples/*", "terraform_templates/*"],
    },
    entry_points={
        "console_scripts": [
            "flocker-config = unofficial_flocker_tools.config:main",
            "flocker-install = unofficial_flocker_tools.install:_main",
            "flocker-plugin-install = unofficial_flocker_tools.plugin:main",
            "flocker-sample-files = unofficial_flocker_tools.sample_files:main",
            "flocker-volumes = unofficial_flocker_tools.flocker_volumes:_main",
            "flocker-get-nodes= unofficial_flocker_tools.get_nodes:main",
            "flocker-destroy-nodes = unofficial_flocker_tools.destroy_nodes:main",
        ],
    },
    version="0.5",
    description="Unofficial tools to make installing and using Flocker easier and more fun.",
    author="Luke Marsden",
    author_email="luke@clusterhq.com",
    url="https://github.com/ClusterHQ/unofficial-flocker-tools",
    install_requires=[
        "PyYAML>=3",
        "Twisted>=14",
        "treq>=14",
        "pyasn1>=0.1",
    ],
)

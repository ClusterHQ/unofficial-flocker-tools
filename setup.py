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
            "hatch = hatch.hatch:_main", # async
            "flockerctl = unofficial_flocker_tools.flocker_volumes:_main", # async
            "flocker-get-diagnostics = unofficial_flocker_tools.diagnostics:_main", #async
            "volume-hub-agents-install = unofficial_flocker_tools.hub_agents:_main", # async
        ],
    },
    version="0.6",
    description="Tools to make installing and using Flocker easier and more fun.",
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

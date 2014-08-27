import setuptools
from setuptools import find_packages


requires = [
    'eventlet',
    'oslo.config',
    'oslo.messaging',
    'ryu',
]


setuptools.setup(
    name='manticore',
    version='0.1',
    packages=find_packages(),
    install_requires=requires,
    entry_points="""
    [console_scripts]
    manticore-l3-agent=manticore.l3_agent:main
    manticore-bgp-speaker=manticore.bgp:main
    """
)

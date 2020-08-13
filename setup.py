from setuptools import (
    find_packages,
    setup,
)


setup(
    name="node",
    version="0.1.0",
    description="Exchanges libs for cas",
    author="Crypto Assistant System",
    packages=find_packages(exclude=("tests", "tests.*")),
    install_requires=["numpy", "sqlalchemy", "aiohttp", "aiohttp_proxy"],
)

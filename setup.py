from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in lava_attach_files/__init__.py
from lava_attach_files import __version__ as version

setup(
	name="lava_attach_files",
	version=version,
	description="copy files and attach to specific doctype",
	author="info@lavaloon.com",
	author_email="info@lavaloon.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)

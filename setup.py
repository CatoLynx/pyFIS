from setuptools import setup, find_packages

metadata = {}
with open('pyfis/metadata.py') as f:
	exec(f.read(), metadata)

setup(
	name = metadata['name'],
	version = metadata['version'],
	description = metadata['description'],
	license = metadata['license'],
	author = metadata['author'],
	author_email = metadata['author_email'],
	install_requires = metadata['requires'],
	url = metadata['url'],
	keywords = metadata['keywords'],
	packages = find_packages(),
)

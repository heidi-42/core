from setuptools import setup, find_namespace_packages

setup(name='heidi',
      version='2.1.0',
      url='https://github.com/KzmnbrS/heidi-core',
      author='KzmnbrS',
      author_email='kzmnbrs@icloud.com',
      license='GNU GENERAL PUBLIC LICENSE VERSION 3',
      install_requires=[
          'aiohttp==3.6.2',
          'gino~=1.0.1',
          'keyring~=21.2.1',
          'aioredis~=1.3.1',
          'jsonschema~=3.2.0',
          'dotmap~=1.3.17',
      ],
      package_dir={"": "src"},
      packages=find_namespace_packages(where="src"))

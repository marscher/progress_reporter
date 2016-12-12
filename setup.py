from setuptools import setup, find_packages
import versioneer

CLASSIFIERS = \
"""Development Status :: 5 - Production/Stable
Environment :: Console
Environment :: Web Environment
Intended Audience :: Developers
License :: OSI Approved :: MIT License
Natural Language :: English
Operating System :: POSIX
Operating System :: Microsoft :: Windows
Programming Language :: Python :: 2.7
Programming Language :: Python :: 3
Topic :: Software Development :: User Interfaces
Topic :: Software Development :: Widget Sets
Topic :: Utilities"""

with open('README.rst') as f:
    long_description = f.read()

kw = dict(name='progress-reporter',
          long_description=long_description,
          version=versioneer.get_version(),
          cmdclass=versioneer.get_cmdclass(),
          classifiers=[c for c in CLASSIFIERS.split('\n')],
          packages=find_packages(),
          package_data={'progress_reporter.tests': ['*.ipynb']},
          url='https://github.com/marscher/progress_reporter',
          keywords=['progress', 'reporting', 'eta', 'gui'],
          license='MIT',
          )

setup(**kw)

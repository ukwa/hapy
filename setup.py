import subprocess
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

def get_version():
    try:
        return subprocess.check_output(['git', 'describe', '--tags', '--always']).strip()
    except:
        return "?.?.?"


setup(
    name = 'hapy-heritrix',
    packages = ['hapy'],
    version=get_version(),
    install_requires=requirements,
    include_package_data=True,
    description = 'A Python wrapper around the Heritrix v3 API',
    license = open('LICENSE').read(),
    author = 'William Mayor, Andrew Jackson',
    author_email = 'w.mayor@ucl.ac.uk, andrew.jackson@bl.uk',
    url = 'https://github.com/ukwa/hapy',
    udownload_urlrl = 'https://github.com/ukwa/hapy',
    keywords = ['heritrix'],
    classifiers = [
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        ],
    entry_points={
        'console_scripts': [
            'h3cc=hapy.h3cc:main',
        ]
    }
)

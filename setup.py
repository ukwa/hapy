import subprocess
from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

def get_version():
    try:
        return subprocess.check_output(['git', 'describe', '--tags', '--always']).strip().decode("utf-8")
    except:
        return "?.?.?"

setup(
    name = 'hapy-heritrix',
    packages=find_packages(),
    version=get_version(),
    install_requires=requirements,
    package_data = {
        '': ['*.groovy']
    },
    description = 'A Python wrapper around the Heritrix v3 API',
    long_description=open('README.md').read(),
    license = open('LICENSE').read(),
    author = 'William Mayor, Andrew Jackson',
    author_email = 'w.mayor@ucl.ac.uk, andrew.jackson@bl.uk',
    url = 'https://github.com/ukwa/hapy',
    download_url = 'https://github.com/ukwa/hapy',
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
            'h3cc=hapy.h3cc:main'
        ]
    }
)

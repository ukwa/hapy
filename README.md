hapy
====

[![Build Status](https://travis-ci.org/WilliamMayor/hapy.png?branch=master)](https://travis-ci.org/WilliamMayor/hapy)

A Python wrapper around the Heritrix API.

Uses Heritrix API 3.x as described here: https://webarchive.jira.com/wiki/display/Heritrix/Heritrix+3.x+API+Guide

## Installation

The easiest way is to install using pip:

    pip install hapy-heritrix

### Without Pip

If you don't want to use pip something like the following should work:

    wget https://github.com/WilliamMayor/hapy/archive/master.zip
    unzip master.zip
    cd hapy-master
    python setup.py install

## Usage

The function calls mirror those of the API, here's an example of how to create a job:

    import hapy

    try:
        h = hapy.Hapy('https://localhost:8443')
        h.create_job('example')
    except hapy.HapyException as he:
        print 'something went wrong:', he.message

Here's the entire API:

    h.create_job(name)
    h.add_job_directory(path)
    h.build_job(name)
    h.launch_job(name)
    h.rescan_job_directory()
    h.pause_job(name)
    h.unpause_job(name)
    h.terminate_job(name)
    h.teardown_job(name)
    h.copy_job(src_name, dest_name, as_profile)
    h.checkpoint_job(name)
    h.execute_script(name, engine, script)
    h.submit_configuration(name, cxml)

There are some extra functions that wrap the undocumented API:

    h.get_info()
    h.get_job_info(name)
    h.get_job_configuration(name)
    h.delete_job(name) (careful with this one, it's not fully tested)

The functions `get_info` and `get_job_info` return a python `dict` that contains the XML returned by Heritrix. `get_job_configuration` returns a string containing the CXML configuration.

For example, here's how to get the launch count of a job named 'test':

    import hapy

    try:
        h = hapy.Hapy('https://localhost:8443', username='admin', password='admin')
        info = h.get_job_info('test')
        launch_count = int(info['job']['launchCount'])
        print 'test has been launched %d time(s)' % launch_count
    except hapy.HapyException as he:
        print 'something went wrong:', he.message

## Example

Here's a quick script that builds, launches and unpauses a job using information from the command line.

    import sys
    import time
    import hapy

    def wait_for(h, job_name, func_name):
        print 'waiting for', func_name
        info = h.get_job_info(job_name)
        while func_name not in info['job']['availableActions']['value']:
            time.sleep(1)
            info = h.get_job_info(job_name)

    name = sys.argv[1]
    config_path = sys.argv[2]
    with open(config_path, 'r') as fd:
        config = fd.read()
    h = hapy.Hapy('https://localhost:8443', username='admin', password='admin')
    h.create_job(name)
    h.submit_configuration(name, config)
    wait_for(h, name, 'build')
    h.build_job(name)
    wait_for(h, name, 'launch')
    h.launch_job(name)
    wait_for(h, name, 'unpause')
    h.unpause_job(name)

## Command-line Interface

### h3cc - Heritrix3 Crawl Controller

Script to interact with Heritrix directly, to perform some general crawler operations.

The ```info-xml``` command downloads the raw XML version of the job information page, which can the be filtered by other tools to extract information. For example, the Java heap status can be queried like this:

    $ python agents/h3cc.py info-xml | xmlstarlet sel -t -v "//heapReport/usedBytes"

Similarly, the number of novel URLs stored in the WARCs can be determined from:

    $ python agents/h3cc.py info-xml | xmlstarlet sel -t -v "//warcNovelUrls"

You can query the frontier too. To see the URL queue for a given host, use a query-url corresponding to that host, e.g.

    $ python agents/h3cc.py -H 192.168.99.100 -q "http://www.bbc.co.uk/" -l 5 pending-urls-from

This will show the first five URLs that are queued to be crawled next on that host. Similarly, you can ask for information about a specific URL:

    $ python agents/h3cc.py -H 192.168.99.100 -q "http://www.bbc.co.uk/news" url-status

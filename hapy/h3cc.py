#!/usr/bin/env python
# encoding: utf-8
'''
agents.h3cc -- Heritrix3 Crawl Controller

agents.h3cc is a tool for controlling Heritrix3, performing basic operations like starting 
and stopping crawls, reporting on crawler status, or updating crawler configuration.

Contains some scripts taken from or based on those here: 

https://webarchive.jira.com/wiki/display/Heritrix/Heritrix3+Useful+Scripts

@author:	 Andrew Jackson

@copyright:  2016 The British Library.

@license:	Apache 2.0

@contact:	Andrew.Jackson@bl.uk
@deffield	updated: 2016-01-16
'''

import sys
import os
import logging
import hapy
import json

# Prevent cert warnings
# See also https://urllib3.readthedocs.io/en/latest/advanced-usage.html#ssl-warnings
import requests.packages.urllib3
requests.packages.urllib3.disable_warnings()

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"..")))

from jinja2 import Environment, PackageLoader
env = Environment(loader=PackageLoader('hapy.h3cc', 'scripts'))

__all__ = []
__version__ = 0.1
__date__ = '2016-01-16'
__updated__ = '2016-01-16'

# Set up a logging handler:
handler = logging.StreamHandler()
#handler = logging.StreamHandler(sys.stdout) # To use stdout rather than the default stderr
formatter = logging.Formatter( "[%(asctime)s] %(levelname)s %(filename)s.%(funcName)s@%(lineno)d: %(message)s" )
handler.setFormatter( formatter ) 

# Attach to root logger
logging.root.addHandler( handler )

# Set default logging output for all modules.
logging.root.setLevel( logging.WARNING )

# Set logging for this module and keep the reference handy:
logger = logging.getLogger( __name__ )
logger.setLevel( logging.INFO )


#
def main(argv=None):
    """
        h3cc

        Command crawler control.
        """

    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    #program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_shortdesc = __import__('__main__').__doc__
    program_license = '''%s

  Created by Andrew Jackson on %s.
  Copyright 2016 The British Library.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-v", "--verbose", dest="verbose", action="count", help="set verbosity level [default: %(default)s]", default=0)
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument('-j', '--job', dest='job', default='frequent',
                            help="Name of job to operate upon. [default: %(default)s]")
        parser.add_argument('-H', '--host', dest='host', default='localhost',
                            help="Name of host to connect to. [default: %(default)s]")
        parser.add_argument('-P', '--port', dest='port', default='8443',
                            help="Secure port to connect to. [default: %(default)s]")
        parser.add_argument('-u', '--user', dest='user',
                            type=str, default="heritrix",
                            help="H3 user to login with [default: %(default)s]" )
        parser.add_argument('-p', '--password', dest='password',
                            type=str, default="heritrix",
                            help="H3 user password [default: %(default)s]" )
        parser.add_argument('-q' '--query-url', dest='query_url', type=str, default='http://www.bbc.co.uk/news',
                            help="URL to use for queries [default: %(default)s]")
        parser.add_argument('-l' '--query-limit', dest='query_limit', type=int, default=10,
                            help="Maximum number of results to return from queries [default: %(default)s]")
        parser.add_argument(dest="command", help="Command to carry out, 'list-jobs', 'status', 'job-status', 'job-info', 'job-info-json', job-cxml', 'surt-scope', 'pending-urls', 'pending-urls-from', 'show-all-sheets', 'show-decide-rules', 'show-metadata', 'kill-all-toethreads'. [default: %(default)s]", metavar="command")

        # Process arguments
        args = parser.parse_args()

        # Up the logging
        verbose = args.verbose
        if verbose > 0:
            logger.setLevel( logging.DEBUG )

        # talk to h3:
        ha = hapy.Hapy("https://%s:%s" % (args.host, args.port), username=args.user, password=args.password)
        job = args.job

        # Commands:
        command = args.command
        if command == "status":
            print(ha.get_info())
        elif command == "list-jobs":
            # FIXME Cope when singular hash or array of hashes
            j = ha.get_info()['engine']['jobs']['value']
            print(j['key'])
        elif command == "job-summary":
            # FIXME Cope when singular hash or array of hashes
            for j in ha.get_info()['engine']['jobs']['value']:
                if job == j['key']:
                    print(j)
        elif command == "job-build":
            ha.build_job(job)
        elif command == "job-launch":
            ha.launch_job(job)
        elif command == "job-resume":
            ha.launch_from_latest_checkpoint(job)
        elif command == "job-pause":
            ha.pause_job(job)
        elif command == "job-unpause":
            ha.unpause_job(job)
        elif command == "job-checkpoint":
            ha.checkpoint_job(job)
        elif command == "job-terminate":
            ha.terminate_job(job)
        elif command == "job-teardown":
            ha.teardown_job(job)
        elif command == "job-status":
            print(ha.get_job_info(job)['job']['statusDescription'])
        elif command == "job-info":
            print(ha.get_job_info(job))
        elif command == "job-info-json":
            print(json.dumps(ha.get_job_info(job), indent=4))
        elif command == "job-cxml":
            print(ha.get_job_configuration(job))
        elif command in ["surt-scope", "show-decide-rules", "show-all-sheets", "show-metadata", "kill-all-toethreads"]:
            template = env.get_template('%s.groovy' % command)
            r = ha.execute_script(engine="groovy", script=template.render(), name=job)
            print(r[0])
        elif command in ["pending-urls", "pending-urls-from", "url-status"]:
            template = env.get_template('%s.groovy' % command)
            r = ha.execute_script(engine="groovy", script=template.render({ "url": args.query_url ,"limit": args.query_limit }), name=job)
            print(r[0])
        else:
            logger.error("Can't understand command '%s'" % command)

        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception as e:
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        logger.exception(e)
        return 2

if __name__ == "__main__":
    sys.exit(main())


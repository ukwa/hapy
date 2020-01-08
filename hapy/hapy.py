import os

from pkg_resources import resource_string
from xml.etree import ElementTree

import requests
import requests.auth
import logging

logger = logging.getLogger(__name__)

HEADERS = {
    'accept': 'application/xml'
}


class HapyException(Exception):

    def __init__(self, r):
        super(HapyException, self).__init__(
            ('HapyException: '
             'request(url=%s, method=%s, data=%s), '
             'response(code=%d, text=%s)') % (
                r.url, r.request.method, r.request.body,
                r.status_code, r.text
            )
        )


class Hapy:

    def __init__(self, base_url, username=None, password=None, insecure=True, timeout=None):
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        self.base_url = '%s/engine' % base_url
        if None not in [username, password]:
            self.auth = requests.auth.HTTPDigestAuth(username, password)
        else:
            self.auth = None
        self.insecure = insecure
        self.timeout = timeout

    def _http_post(self, url, data, code=200):
        r = requests.post(
            url=url,
            data=data,
            headers=HEADERS,
            auth=self.auth,
            verify=not self.insecure,
            allow_redirects=False,
            timeout=self.timeout
        )
        self.lastresponse = r
        if r.status_code != code:
            raise HapyException(r)
        return r

    def _http_get(self, url, code=200):
        r = requests.get(
            url=url,
            headers=HEADERS,
            auth=self.auth,
            verify=not self.insecure,
            timeout=self.timeout
        )
        self.lastresponse = r
        if r.status_code != code:
            raise HapyException(r)
        return r

    def _http_put(self, url, data, code=200):
        r = requests.put(
            url=url,
            data=data,
            headers=HEADERS,
            auth=self.auth,
            verify=not self.insecure,
            timeout=self.timeout
        )
        self.lastresponse = r
        if r.status_code != code:
            raise HapyException(r)
        return r

    def create_job(self, name):
        self._http_post(
            url=self.base_url,
            data=dict(
                action='create',
                createpath=name
            ),
            code=303
        )

    def add_job_directory(self, path):
        self._http_post(
            url=self.base_url,
            data=dict(
                action='add',
                path=path
            ),
            code=303
        )

    def build_job(self, name):
        self._http_post(
            url='%s/job/%s' % (self.base_url, name),
            data=dict(
                action='build'
            ),
            code=303
        )

    def launch_job(self, name):
        self._http_post(
            url='%s/job/%s' % (self.base_url, name),
            data=dict(
                action='launch'
            ),
            code=303
        )

    def rescan_job_directory(self):
        self._http_post(
            url=self.base_url,
            data=dict(
                action='rescan'
            ),
            code=303
        )

    def pause_job(self, name):
        self._http_post(
            url='%s/job/%s' % (self.base_url, name),
            data=dict(
                action='pause'
            ),
            code=303
        )

    def unpause_job(self, name):
        self._http_post(
            url='%s/job/%s' % (self.base_url, name),
            data=dict(
                action='unpause'
            ),
            code=303
        )

    def terminate_job(self, name):
        self._http_post(
            url='%s/job/%s' % (self.base_url, name),
            data=dict(
                action='terminate'
            ),
            code=303
        )

    def teardown_job(self, name):
        self._http_post(
            url='%s/job/%s' % (self.base_url, name),
            data=dict(
                action='teardown'
            ),
            code=303
        )

    def copy_job(self, src_name, dest_name, as_profile=False):
        data = dict(copyTo=dest_name)
        if as_profile:
            data['asProfile'] = 'on'
        self._http_post(
            url='%s/job/%s' % (self.base_url, src_name),
            data=data,
            code=303
        )

    def checkpoint_job(self, name):
        self._http_post(
            url='%s/job/%s' % (self.base_url, name),
            data=dict(
                action='checkpoint'
            ),
            code=303
        )

    def execute_script(self, name, engine, script):
        r = self._http_post(
            url='%s/job/%s/script' % (self.base_url, name),
            data=dict(
                engine=engine,
                script=script
            ),
            code=200
        )
        tree = ElementTree.fromstring(r.content)
        raw = tree.find('rawOutput')
        if raw is not None:
            raw = raw.text
        html = tree.find('htmlOutput')
        if html is not None:
            html = html.text
        return raw, html

    def submit_configuration(self, name, cxml):
        info = self.get_job_info(name)
        url = info['job']['primaryConfigUrl']
        self._http_put(
            url=url,
            data=cxml,
            code=200
        )

    # End of documented API calls, here are some useful extras

    def __tree_to_dict(self, tree):
        if len(tree) == 0:
            return {tree.tag: tree.text}
        D = {}
        for child in tree:
            d = self.__tree_to_dict(child)
            tag = next(iter(d))
            try:
                try:
                    D[tag].append(d[tag])
                except AttributeError:
                    D[tag] = [D[tag], d[tag]]
            except KeyError:
                D[tag] = d[tag]
        return {tree.tag: D}

    def get_info(self):
        r = self._http_get(self.base_url)
        return self.__tree_to_dict(ElementTree.fromstring(r.content))

    def get_job_info(self, name):
        r = self._http_get('%s/job/%s' % (self.base_url, name))
        return self.__tree_to_dict(ElementTree.fromstring(r.content))

    def get_job_configuration(self, name):
        info = self.get_job_info(name)
        url = info['job']['primaryConfigUrl']
        r = self._http_get(
            url=url
        )
        return r.content

    def delete_job(self, name):
        script = resource_string(__name__, 'scripts/delete_job.groovy')
        self.execute_script(name, 'groovy', script)
        info = self.get_info()
        jdir = info['engine']['jobsDir']
        jobpath = os.path.join(jdir, '%s.jobpath' % name)
        if os.path.isfile(jobpath):
            os.remove(jobpath)
        self.rescan_job_directory()

    def status(self, job=""):
        info = self.get_job_info(job)
        if info.has_key('job'):
            status = info['job'].get("crawlControllerState", "")
        else:
            status = ""
        return status

    def list_jobs(self, status=None):
        r = self._http_get(self.base_url)
        xml = ElementTree.fromstring(r.content)
        if status is None:
            return [job.find("shortName").text for job in xml.xpath("//jobs/value")]
        else:
            return [job.find("shortName").text for job in xml.xpath("//jobs/value[./crawlControllerState = '%s']" % status)]

    def get_launch_id(self, job=""):
        raw, html = self.execute_script(job,"groovy","rawOut.println( appCtx.getCurrentLaunchId() );")
        if raw:
            raw = raw.strip()
        return raw

    def get_seeds( self, job ):
        url = "%s/job/%s/jobdir/latest/seeds.txt" % ( self.host, job )
        r = requests.get( url, auth=requests.auth.HTTPDigestAuth( self.user, self.passwd ), verify=self.verify )
        seeds = [ seed.strip() for seed in r.iter_lines() ]
        for i, seed in enumerate( seeds ):
            if seed.startswith( "#" ):
                return seeds[ 0:i ]
        return seeds

    def empty_frontier( self, job ):
        script = "count = job.crawlController.frontier.deleteURIs( \".*\", \"^.*\" )\nrawOut.println count"
        xml = self.execute_script(job, "groovy", script)
        tree = ElementTree.fromstring( xml.content )
        return tree.find( "rawOutput" ).text.strip()

    def launch_from_latest_checkpoint(self, job):
        info = self.get_job_info(job)
        if info.has_key('job'):
            checkpoints = info['job'].get("checkpointFiles").get("value", [])
        else:
            checkpoints = []

        if len(checkpoints) == 0:
            logger.info("No checkpoint found. Lauching as new job...")
            self.launch_job(job)
        else:
            # Select the most recent checkpoint:
            if isinstance(checkpoints, list):
                checkpoint = checkpoints[0]
            else:
                # H3 doesn't return an array if there is only one checkpoint!
                checkpoint = checkpoints
            logger.info("Launching from checkpoint %s..." %  checkpoint)
            # And launch:
            self._http_post(
                url='%s/job/%s' % (self.base_url, job),
                data=dict(
                    action='launch',
                    checkpoint=checkpoint
                ),
                code=303
            )

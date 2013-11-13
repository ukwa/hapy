import os

from pkg_resources import resource_string
from xml.etree import ElementTree

import requests


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

    def __init__(self, base_url, username=None, password=None, insecure=True):
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        self.base_url = base_url
        if None not in [username, password]:
            self.auth = requests.auth.HTTPDigestAuth(username, password)
        else:
            self.auth = None
        self.insecure = insecure

    def __http_post(self, url, data):
        r = requests.post(
            url=url,
            data=data,
            headers=HEADERS,
            auth=self.auth,
            verify=not self.insecure,
            allow_redirects=False
        )
        self.lastresponse = r
        if r.status_code not in [200, 303, 307]:
            raise HapyException(r)
        return r

    def __http_get(self, url):
        r = requests.get(
            url=url,
            headers=HEADERS,
            auth=self.auth,
            verify=not self.insecure
        )
        self.lastresponse = r
        if r.status_code != 200:
            raise HapyException(r)
        return r

    def __http_put(self, url, data):
        r = requests.put(
            url=url,
            data=data,
            headers=HEADERS,
            auth=self.auth,
            verify=not self.insecure
        )
        self.lastresponse = r
        if r.status_code != 200:
            raise HapyException(r)
        return r

    def create_job(self, name):
        self.__http_post(
            url=self.base_url,
            data=dict(
                action='create',
                createpath=name
            )
        )

    def add_job_directory(self, path):
        self.__http_post(
            url=self.base_url,
            data=dict(
                action='add',
                addpath=path
            )
        )

    def build_job(self, name):
        self.__http_post(
            url='%s/job/%s' % (self.base_url, name),
            data=dict(
                action='build'
            )
        )

    def launch_job(self, name):
        self.__http_post(
            url='%s/job/%s' % (self.base_url, name),
            data=dict(
                action='launch'
            )
        )

    def rescan_job_directory(self):
        self.__http_post(
            url=self.base_url,
            data=dict(
                action='rescan'
            )
        )

    def pause_job(self, name):
        self.__http_post(
            url='%s/job/%s' % (self.base_url, name),
            data=dict(
                action='pause'
            )
        )

    def unpause_job(self, name):
        self.__http_post(
            url='%s/job/%s' % (self.base_url, name),
            data=dict(
                action='unpause'
            )
        )

    def terminate_job(self, name):
        self.__http_post(
            url='%s/job/%s' % (self.base_url, name),
            data=dict(
                action='terminate'
            )
        )

    def teardown_job(self, name):
        self.__http_post(
            url='%s/job/%s' % (self.base_url, name),
            data=dict(
                action='teardown'
            )
        )

    def copy_job(self, src_name, dest_name, as_profile=False):
        data = dict(copyTo=dest_name)
        if as_profile:
            data['asProfile'] = 'on'
        self.__http_post(
            url='%s/job/%s' % (self.base_url, src_name),
            data=data
        )

    def checkpoint_job(self, name):
        self.__http_post(
            url='%s/job/%s' % (self.base_url, name),
            data=dict(
                action='checkpoint'
            )
        )

    def execute_script(self, name, engine, script):
        r = self.__http_post(
            url='%s/job/%s/script' % (self.base_url, name),
            data=dict(
                engine=engine,
                script=script
            )
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
        self.__http_put(
            url='%s/job/%s/jobdir/crawler-beans.cxml' % (self.base_url, name),
            data=cxml
        )

    # End of documented API calls, here are some useful extras

    def __tree_to_dict(self, tree, root=True):
        if len(tree) == 0:
            return tree.tag, tree.text
        d = {}
        for child in tree:
            tag, contents = self.__tree_to_dict(child, root=False)
            try:
                try:
                    d[tag].append(contents)
                except AttributeError:
                    d[tag] = [d[tag], contents]
            except KeyError:
                d[tag] = contents
        if root:
            return d
        return tree.tag, d

    def get_info(self):
        r = self.__http_get(self.base_url)
        return self.__tree_to_dict(ElementTree.fromstring(r.content))

    def get_job_info(self, name):
        r = self.__http_get('%s/job/%s' % (self.base_url, name))
        return self.__tree_to_dict(ElementTree.fromstring(r.content))

    def get_job_configuration(self, name):
        r = self.__http_get(
            url='%s/job/%s/jobdir/crawler-beans.cxml' % (self.base_url, name)
        )
        return r.content

    def delete_job(self, name):
        script = resource_string(__name__, 'scripts/delete_job.groovy')
        self.execute_script(name, 'groovy', script)
        info = self.get_info()
        jdir = info['jobsDir']
        jobpath = os.path.join(jdir, '%s.jobpath' % name)
        if os.path.isfile(jobpath):
            os.remove(jobpath)
        self.rescan_job_directory()

    def get_jobs(self):
        info = self.get_info()
        value = info['jobs']['value']
        if isinstance(value, list):
            return value
        return [value]

    def get_job_status(self, name):
        info = self.get_job_info(name)
        try:
            return info['crawlControllerState']
        except:
            return info['statusDescription']

import json
from hapy.dash.collector import Heritrix3Collector
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST, REGISTRY
from flask import Flask
from flask import render_template, redirect, url_for, request, Response, send_file, abort
app = Flask(__name__)


@app.route('/')
def status():

    c = Heritrix3Collector()
    s = c.run_api_requests()

    # Log collected data:
    app.logger.info(json.dumps(s, indent=4))

    # And render
    return render_template('dashboard.html', title="Status", crawls=s)


@app.route('/metrics')
def prometheus_metrics():
    REGISTRY.register(Heritrix3Collector())

    headers = {'Content-Type': CONTENT_TYPE_LATEST}
    return generate_latest(REGISTRY), 200, headers
#

@app.route('/control/dc/pause')
def pause_dc():
    servers = json.load(systems().servers)
    services = json.load(systems().services)
    for job in ['dc0-2016', 'dc1-2016', 'dc2-2016', 'dc3-2016']:
        server = servers[services['jobs'][job]['server']]
        h = hapyx.HapyX(server['url'], username=server['user'], password=server['pass'])
        h.pause_job(services['jobs'][job]['name'])
    return redirect(url_for('status'))


@app.route('/control/dc/unpause')
def unpause_dc():
    servers = json.load(systems().servers)
    services = json.load(systems().services)
    for job in ['dc0-2016', 'dc1-2016', 'dc2-2016', 'dc3-2016']:
        server = servers[services['jobs'][job]['server']]
        h = hapyx.HapyX(server['url'], username=server['user'], password=server['pass'])
        h.unpause_job(services['jobs'][job]['name'])
    return redirect(url_for('status'))


@app.route('/stop/<frequency>')
def stop(frequency=None):
    if frequency:
        crawl.tasks.stop_start_job(frequency,restart=False)
    return redirect(url_for('status'))


if __name__ == "__main__":
    app.run(debug=True, port=5505)

from flask import Flask, Response, request, redirect, render_template
from functools import wraps
from celery import Celery
import subprocess
import cherrypy
import requests
import uuid
import glob
import json
import os


app = Flask(__name__)

app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

cwd = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.split(cwd)[0]
DATA_DIR = os.path.join(PROJECT_DIR, 'data')

import redis
rdb = redis.StrictRedis(host='localhost', port=6379, db=1)

#------------------------------------------------------------------------
# Define interface function for celery
#

def make_celery(app):
    celery = Celery(app.import_name,broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self,*args,**kwargs):
            with app.app_context():
                return TaskBase.__call__(self,*args,**kwargs)
    celery.Task = ContextTask
    return celery

celery = make_celery(app)


#------------------------------------------------------------------
# Define background tasks
#

@celery.task(name='tasks.download')
def download(ds):
    # Build dataset URL
    base_url = 'http://cs.stanford.edu/people/karpathy/deepimagesent/'
    url = base_url + ds + '.zip'
    # Download the dataset in chunks
    local_filename = url.split('/')[-1]
    outfile_path = os.path.join(DATA_DIR, local_filename)
    r = requests.get(url, stream=True)
    total = r.headers.get('content-length')
    dl = 0
    with open(outfile_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024): 
            if chunk:
                f.write(chunk)
                f.flush()
                dl += len(chunk)
                download.update_state(state='RUNNING', meta={'current': dl, 'total': total})   
    # Unzip the downloaded dataset
    subprocess.call(['unzip', outfile_path, '-d', DATA_DIR])
    # Remove the zip file
    os.remove(outfile_path)
    # Add to list of datasets
    rdb.lpush('downloaded_datasets', ds)
    

@celery.task(name='tasks.train_dataset')
def train_dataset(ds):
    os.chdir('../')
    cmd = ['python', os.path.join(PROJECT_DIR, 'driver.py')]
    cmd += ['--dataset=%s' % ds]
    rdb.hset('training_status', ds, 'RUNNING')
    #try:
    subprocess.call(cmd)
    rdb.hset('training_status', ds, 'SUCCESS')
    #except:
    #    rdb.hset('training_status', ds, 'FAILURE')
    

@celery.task(name='tasks.execute_training')
def execute_training():
    dks = 'downloaded_datasets'
    dds = rdb.lrange(dks, 0, rdb.llen(dks))
    tstats = rdb.hgetall('training_status')
    datasets = set(dds) - set(tstats.keys())
    datasets = list(datasets)
    for ds in datasets:
        train_dataset.delay(ds)
    
    
@celery.task(name='tasks.test_func')
def test_func():
    import time
    for i in range(10):
        time.sleep(2)
        test_func.update_state(state='RUNNING', meta={'current': i})
        

#------------------------------------------------------------------
# Define authentication functions
#

def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid."""
    return username == 'admin' and password == 'default2015'

def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated
    
    
#------------------------------------------------------------------
# Define view functions
#
    

@app.route("/")
@requires_auth
def home():
    dsk = 'downloaded_datasets'
    ds = rdb.lrange(dsk, 0, rdb.llen(dsk))
    ds_list = ['flickr8k', 'flickr30k', 'coco']
    nds = set(ds_list) - set(ds)
    return render_template('home.html', datasets=ds, for_download=list(nds)[::-1])


@app.route("/download/")
@requires_auth
def download_datasets():
    ds = request.args['dataset']
    task_id = str(uuid.uuid4())
    download.apply_async(args=(ds,), task_id=task_id)
    return render_template('home.html', task_id=task_id, dataset=ds)
    
    
@app.route("/download_status/")
@requires_auth
def download_status():
    task_id = request.args['id']
    job = download.AsyncResult(task_id)
    if job.state == 'RUNNING':
        pct = job.info['current']/float(job.info['total'])
        pct = int(round(pct * 100, 2))
    elif job.state == 'SUCCESS':
        pct = 100
    else:
        pct = 0
    return str(pct)


@app.route("/train/")
@requires_auth
def train():
    execute_training.delay()
    return redirect('/monitor/')
    

@app.route("/monitor/")
@requires_auth
def monitor():
    return render_template('monitorcv.html')
   
   
@app.route("/results/")
@requires_auth
def results():
    return render_template('visualize_result_struct.html')
    
    
@app.route("/workers/")
@requires_auth
def workers_info():
    action = request.args['action']
    if action == 'list':
        tk = 'training_workers'
        workers = rdb.lrange(tk, 0, rdb.llen(tk))
        return json.dumps(workers)
    elif action == 'status':
        wid = request.args['id']
        status = rdb.get('%s_status' % wid)
        return json.dumps(status)
        

if __name__ == "__main__":

    debug = True
    
    if debug:
        app.run(debug=True)
    else:
        cherrypy.tree.graft(app, '/')
        cherrypy.tree.mount(None, '/static', {'/' : {
            'tools.staticdir.dir': app.static_folder,
            'tools.staticdir.on': True,
            }})
        cherrypy.config.update({
            'server.socket_port': 5000,
            })
        cherrypy.engine.start()
        cherrypy.engine.block()

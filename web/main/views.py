from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import logout
from django.conf import settings
from tasks import download
from models import Task
import uuid
import os


@login_required
def home_page(request):
    dsk = 'downloaded_datasets'
    dls = Task.objects.filter(task_type='download_dataset', status='SUCCESS')
    ds = []
    if dls:
        ds = [x.data_input for x in dls]
    ds_list = ['flickr8k', 'flickr30k', 'coco']
    nds = set(ds_list) - set(ds)
    context = {
        'datasets': ds,
        'for_download': list(nds)[::-1]
    }
    return render_to_response('main/home.html', context)
    

@login_required
def logout_user(request):
    logout(request)
    return HttpResponseRedirect('/')
    

def download_datasets(request):
    ds = request.GET.get('dataset')
    task_id = str(uuid.uuid4())
    job = Task(task_id=task_id, task_type='download_dataset', data_input=ds)
    job.save()
    download.apply_async(args=(ds, job), task_id=task_id)
    context = {'task_id': task_id, 'dataset': ds}
    return render_to_response('main/home.html', context)
    
    
def download_status(request):
    task_id = request.GET.get('id')
    job = download.AsyncResult(task_id)
    if job.state == 'RUNNING':
        pct = job.info['current']/float(job.info['total'])
        pct = int(round(pct * 100, 2))
    elif job.state == 'SUCCESS':
        pct = 100
    else:
        pct = 0
    return HttpResponse(pct)


def train(request):
    execute_training.delay()
    return HttpResponseRedirect('/monitor/')
    

def monitor(request):
    return render_to_response('main/monitorcv.html')
   

def get_results(request):
    res_file = os.path.join(settings.PROJECT_DIR, 'result_struct.json')
    return HttpResponse(open(res_file, 'r'), content_type = 'application/json; charset=utf8')
    

def serve_image(request, dataset, img_id):
    imgs_dir = os.path.join(settings.PROJECT_DIR, 'data', dataset, 'imgs')
    img_file = os.path.join(imgs_dir, img_id + '.jpg')
    return HttpResponse(open(img_file,'rb'), content_type='image/jpeg')    
    
   
def results(request):
    return render_to_response('main/visualize_result_struct.html')
    
    
#@app.route("/workers/")
#@requires_auth
def workers_info(request):
    action = request.GET.get('action')
    if action == 'list':
        tk = 'training_workers'
        workers = rdb.lrange(tk, 0, rdb.llen(tk))
        return json.dumps(workers)
    elif action == 'status':
        wid = request.GET.get('id')
        status = rdb.get('%s_status' % wid)
        return json.dumps(status)
        
        
#@app.route("/clear/")
#@requires_auth
def stop_and_clear(request):
    # TODO -- revoke and terminate training tasks
    # Clear the status and checkpoint files
    # Clear the status messages in Redis DB
    rk = 'training_tasks'
    for task_id in rdb.lrange(rk, 0, rdb.llen(rk)):
        revoke(task_id, terminate=True)
    rdb.delete('training_tasks')
    rdb.delete('training_status')
    return HttpResponseRedirect('/')

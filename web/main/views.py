from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template.context_processors import csrf
from django.contrib.auth import logout
from tasks import download, execute_training, generate_results
from django.conf import settings
from celery.task.control import revoke
from signal import SIGUSR1
from tasks import download
from models import Task
import json
import uuid
import glob
import os


@login_required
def home_page(request):
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
    

def manage_datasets(request):
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
    return render_to_response('main/datasets.html', context)


def download_datasets(request):
    ds = request.GET.get('dataset')
    task_id = str(uuid.uuid4())
    job = Task(task_id=task_id, task_type='download_dataset', data_input=ds)
    job.save()
    download.apply_async(args=(ds, job), task_id=task_id)
    context = {'task_id': task_id, 'dataset': ds}
    return render_to_response('main/datasets.html', context)
    
    
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
    context = {}
    if request.method == 'POST':
        checkpoint_file = request.POST.get('checkpoint')
        task_id = str(uuid.uuid4())
        generate_results.apply_async(args=(checkpoint_file,), task_id=task_id)
        return HttpResponseRedirect('/results/?id=%s' % task_id)
    elif request.method == 'GET':
        task_id = request.GET.get('id')
        if task_id:
            context = {'task_id': task_id}
        else:
            checkpoints_dir = os.path.join(settings.PROJECT_DIR, 'cv')
            chkp_files = glob.glob(os.path.join(checkpoints_dir, '*.p'))
            context = {'files': [os.path.basename(x) for x in chkp_files]}
    context.update(csrf(request))
    return render_to_response('main/results.html', context)


def predict(request):
    context = {}
    return render_to_response('main/predict.html', context)


def workers_info(request):
    action = request.GET.get('action')
    if action == 'list':
        ss = ['RUNNING', 'PENDING', 'FAILURE']
        ts = Task.objects.filter(task_type='train_dataset', status__in=ss)
        ts_list = [x.task_id for x in ts]
        return HttpResponse(json.dumps(ts_list), content_type='application/json')
    elif action == 'status':
        wid = request.GET.get('id')
        status_dir = os.path.join(settings.PROJECT_DIR, 'status')
        status_file = os.path.join(status_dir, '%s_status.json' % wid)
        return HttpResponse(open(status_file,'r'), content_type='application/json')


def stop_and_clear(request):
    ts = Task.objects.filter(task_type='train_dataset')
    for t in ts:
        if t.status == 'RUNNING':
            revoke(t.task_id, terminate=True, signal=SIGUSR1)
        t.delete()
    status_files = glob.glob(os.path.join(settings.PROJECT_DIR, 'status', '*.json'))
    checkpoint_files = glob.glob(os.path.join(settings.PROJECT_DIR, 'cv', '*.p'))
    xfiles = status_files + checkpoint_files
    for f in xfiles:
        os.remove(f)
    return HttpResponseRedirect('/')

from django.conf import settings
from collections import defaultdict
from models import Task
from celery import task
import subprocess
import requests
import glob
import uuid
import os
import time

DATA_DIR = os.path.join(settings.PROJECT_DIR, 'data')

#------------------------------------------------------------------
# Define background tasks
#

@task(name='tasks.download')
def download(ds, job):
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
    # Update the task records
    job.status = 'SUCCESS'
    job.save()
    # Remove the zip file
    os.remove(outfile_path)
    

@task(name='tasks.train_dataset')
def train_dataset(ds, job):
    job.status = 'RUNNING'
    job.save()
    os.chdir(settings.PROJECT_DIR)
    cmd = ['python', os.path.join(settings.PROJECT_DIR, 'driver.py')]
    cmd += ['--dataset=%s' % ds, '--worker_id=%s' % job.task_id]
    cmd += ['--learning_rate=%s' % settings.LEARNING_RATE[ds]]
    task_id = train_dataset.request.id
    subprocess.call(cmd)
    # Update the task records
    job.status = 'SUCCESS'
    job.save()


@task(name='tasks.execute_training')
def execute_training():
    ds_list = ['flickr8k', 'flickr30k', 'coco']
    ts = Task.objects.filter(task_type='train_dataset', status='SUCCESS')
    tss = []
    if ts:
        tss = [x.data_input for x in ts]
    datasets = set(ds_list) - set(tss)
    datasets = list(datasets)
    for ds in datasets:
        jid = str(uuid.uuid1())
        job = Task(task_id=jid, task_type='train_dataset', data_input=ds)
        job.save()
        train_dataset.delay(ds, job)


@task(name='tasks.generate_results')
def generate_results(checkpoint_file):
    jid = generate_results.request.id
    job = Task(
            task_id=jid, 
            task_type='generate_results', 
            data_input=checkpoint_file,
            status='RUNNING'
        )
    job.save()
    os.chdir(settings.PROJECT_DIR)
    checkpoint_path = os.path.join(settings.PROJECT_DIR, 'cv', checkpoint_file)
    cmd = ['python', os.path.join(settings.PROJECT_DIR, 'eval_sentence_predictions.py')]
    cmd += [checkpoint_path]
    subprocess.call(cmd)
    # Update the task records
    job.status = 'SUCCESS'
    job.save()

    
@task(name='tasks.delete_old_checkpoints')
def delete_old_checkpoints():
    checkpoints_dir = os.path.join(settings.PROJECT_DIR, 'cv')
    chkp_files = glob.glob(os.path.join(checkpoints_dir, '*.p'))
    ds_list = ['flickr8k', 'flickr30k', 'coco']
    for ds in ds_list:
        fmap = defaultdict(list)
        for cf in chkp_files:
            fname = os.path.split(cf)[-1]
            fname_split = fname.split('_')
            fds = fname_split[2]
            if ds == fds:
                chk_num = fname_split[-1].split('.')[0]
                fmap[int(chk_num)].append(cf)
        fmap_keys = fmap.keys()
        if len(fmap_keys) > 1:
            fmap_keys.sort(reverse=True)
            for k in fmap_keys[1:]:
                for f in fmap[k]:
                    os.remove(f)
    
    
@task(name='tasks.test_func')
def test_func():
    for i in range(10):
        time.sleep(2)
        test_func.update_state(state='RUNNING', meta={'current': i})


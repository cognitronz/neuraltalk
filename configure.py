#!/usr/bin/env python

from subprocess import Popen, PIPE
import os


startup_config = """#!/bin/bash

# Supervisord auto-start
#
# description: Auto-starts supervisord
# processname: supervisord
# pidfile: /var/run/supervisord.pid

SUPERVISORD="/usr/local/bin/supervisord -c {0}/supervisord.conf"
SUPERVISORCTL="/usr/local/bin/supervisorctl -c {0}/supervisord.conf"

case $1 in
start)
        echo -n "Starting supervisord... "
        $SUPERVISORD
        echo
        ;;
stop)
        echo -n "Stopping supervisord... "
        $SUPERVISORCTL shutdown
        echo
        ;;
restart)
        echo -n "Stopping supervisord... "
        $SUPERVISORCTL shutdown
        echo
        echo -n "Starting supervisord... "
        $SUPERVISORD
        echo
        ;;
control)
        $SUPERVISORCTL
        ;;
esac""".format(os.getcwd())

print 'Setting supervisord as upstart script...'

# Remove if config exists
if os.path.exists('/etc/init.d/supervisord'):
    os.remove('/etc/init.d/supervisord')

# Write the config file
with open('/etc/init.d/supervisord', 'w') as outf:
    outf.write(startup_config)
    cmds = []
    cmds.append('chmod +x /etc/init.d/supervisord')
    cmds.append('update-rc.d -f supervisord remove')
    cmds.append('update-rc.d -f supervisord defaults')
    for cmd in cmds:
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        p.communicate()
        
print 'Startup script added!'  

# Setup the supervisord.conf

supervisord_conf = """
[inet_http_server]
port = 127.0.0.1:8080

[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisord]
logfile = {0}/supervisord.log
logfile_maxbytes = 10MB
loglevel = debug
pidfile = {0}/supervisord.pid
directory = {0}  ; (change this during deployment)
environment = C_FORCE_ROOT="yes"

[supervisorctl]
serverurl = http://localhost:8080

[program:webserver]
directory = web
command = {0}/venv/bin/python manage.py runserver
stopasgroup = true

[program:celery]
directory = web
command = {0}/venv/bin/celery -A web worker -l info
stopasgroup = true

[program:redis]
command = /usr/bin/redis-server
stopasgroup = true
""".format(os.getcwd())

# Remove if config exists
if os.path.exists('supervisord.conf'):
    os.remove('supervisord.conf')

# Write the config file
print 'Writing supervisord.conf file...'
with open('supervisord.conf', 'w') as outf:
    outf.write(supervisord_conf)

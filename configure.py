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

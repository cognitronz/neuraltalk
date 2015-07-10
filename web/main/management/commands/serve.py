#!/usr/bin/env python
# -*- coding: utf-8 -*-
 
import os
import cherrypy
from threading import Timer

from django.core.management.base import BaseCommand, CommandError
 
import django
os.environ["DJANGO_SETTINGS_MODULE"] = "deals_scraper.settings"
django.setup()

from django.conf import settings
from django.core.handlers.wsgi import WSGIHandler
 
 
class DjangoApplication(object):

 
    def mount_static(self, url, root):
        """
        :param url: Relative url
        :param root: Path to static files root
        """
        config = {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': root,
            'tools.expires.on': True,
            'tools.expires.secs': 86400
        }
        cherrypy.tree.mount(None, url, {'/': config})
 
 
    def run(self, host, port):
        cherrypy.config.update({
            'server.socket_host': host,
            'server.socket_port': int(port),
            'engine.autoreload_on': False,
            'log.screen': True
        })
        self.mount_static(settings.STATIC_URL, settings.STATIC_ROOT)
        cherrypy.log("Loading and serving Django application")
        cherrypy.tree.graft(WSGIHandler())
        cherrypy.engine.start()
        cherrypy.engine.block()
 
 
class Command(BaseCommand):

    def handle(self, *args, **options):
        DjangoApplication().run('0.0.0.0', 8000)

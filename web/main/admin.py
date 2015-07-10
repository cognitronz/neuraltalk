from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import ugettext_lazy
from models import Task

"""
class MyAdminSite(AdminSite):
    # Text to put at the end of each page's <title>.
    site_title = ugettext_lazy('Neuraltalk')

    # Text to put in each page's <h1>.
    site_header = ugettext_lazy('Neuraltalk')

    # Text to put at the top of the admin index page.
    index_title = ugettext_lazy('Neuraltalk')

admin_site = MyAdminSite()
"""

class TaskAdmin(admin.ModelAdmin):
    list_display = ('task_id', 'task_type', 'data_input', 'status')
    
admin.site.register(Task, TaskAdmin)

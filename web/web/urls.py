from django.conf.urls import include, url
from django.contrib.auth.views import login
from django.contrib import admin


urlpatterns = [
    url(r'^$', 'main.views.home_page'),
    url(r'^download/$', 'main.views.download_datasets'),
    url(r'^download_status/$', 'main.views.download_status'),
    url(r'^logout/$', 'main.views.logout_user'),
    url(r'^datasets/$', 'main.views.manage_datasets'),
    url(r'^train/$', 'main.views.train'),
    url(r'^monitor/$', 'main.views.monitor'),
    url(r'^results/$', 'main.views.results'),
    url(r'^get_results/$', 'main.views.get_results'),
    url(r'^results/data/(?P<dataset>.*)/imgs/(?P<img_id>.*)\.jpg$', 'main.views.serve_image'),
    url(r'^workers/$', 'main.views.workers_info'),
    url(r'^stop_and_clear/$', 'main.views.stop_and_clear'),
    url(r'^predict/$', 'main.views.predict'),
    url(r'^admin/', include(admin.site.urls)),
]


admin.site.site_header = 'Neuraltalk'

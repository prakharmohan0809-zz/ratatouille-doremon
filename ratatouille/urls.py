from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^hit_me/$', views.hit_me, name='hit_me'),
    url(r'^listen/$', views.listen, name='listen'),
    url(r'^init/$', views.init, name='init'),
]
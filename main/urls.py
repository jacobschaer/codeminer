from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^repository/(?P<repository_id>\w+)/delete', views.delete_repository, name='delete_repository'),
    url(r'^repository/(?P<repository_id>\w+)', views.repository, name='repository'),
    url(r'^repository/add', views.add_repository, name='add_repository')
]
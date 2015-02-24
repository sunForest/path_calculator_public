from django.conf.urls import patterns, url

from graphGeneration import views

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'drawPolygon/', views.drawPolygon, name = 'drawPolygon')
)


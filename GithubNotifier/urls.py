from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^members/(?P<organization>[-\w]+)', views.members, name='members'),
    url(r'^email', views.send_emails_to_nameless_members, name='email'),
    url(r'^save', views.save_nameless_members_to_aws, name='save')
]

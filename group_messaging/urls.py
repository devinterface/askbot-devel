"""url configuration for the group_messaging application"""
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url
from group_messaging import views

urlpatterns = patterns('',
    url(
        '^threads/$',
        views.ThreadsList().as_view(),
        name='get_threads'
    ),
    url(
        '^threads/create/$',
        views.NewThread().as_view(),
        name='create_thread'
    ),
    url(
        '^senders/$',
        views.SendersList().as_view(),
        name='get_senders'
    )
)

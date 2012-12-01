from django.conf.urls import patterns, include, url

urlpatterns = patterns('Gifts.views',
    url(r'^$', 'user_home', name='user_home'),
    url(r'^gift/new/$', 'add_gift', name='add_gift'),
    url(r'^gift/(\d+)/remove/$', 'remove_gift', name='remove_gift'),
    url(r'^user/new/$', 'add_person', name='add_person'),
    url(r'^user/(\d+)/$', 'view_user', name='view_user'),
    url(r'^user/(\d+)/gift/new/$', 'add_secret_gift'),
    url(r'^user/(\d+)/gift/(\d+)/reserve/$', 'reserve_gift', name='reserve_gift'),
    url(r'^user/(\d+)/gift/(\d+)/unreserve/$', 'unreserve_gift', name='unreserve_gift'),
)
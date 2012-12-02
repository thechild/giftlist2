from django.conf.urls import patterns, include, url

urlpatterns = patterns('Gifts.views',
    url(r'^$', 'user_home', name='user_home'),
    url(r'^gift/new/$', 'add_gift', name='add_gift'),
    url(r'^gift/(\d+)/remove/$', 'remove_gift', name='remove_gift'),
    url(r'^gift/(\d+)/edit/$', 'add_gift', name='edit_gift'),
    url(r'^user/new/$', 'add_person', name='add_person'),
    url(r'^user/(\d+)/$', 'view_user', name='view_user'),
    url(r'^user/(\d+)/gift/new/$', 'add_secret_gift'),
    url(r'^user/(\d+)/gift/(\d+)/reserve/$', 'reserve_gift', name='reserve_gift'),
    url(r'^user/(\d+)/gift/(\d+)/unreserve/$', 'unreserve_gift', name='unreserve_gift'),
    url(r'^user/all/$', 'view_all_people', name='view_all_people'),
    url(r'^user/(\d+)/follow/$', 'follow_person', name='follow_person'),
    url(r'^user/(\d+)/unfollow/$', 'unfollow_person', name='unfollow_person'),

    url(r'^account/$', 'manage_account', name='manage_account'),
)
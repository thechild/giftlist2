from django.conf.urls import patterns, include, url
from django.contrib import admin


admin.autodiscover()

import os
import logging
import analytics # segment.io
analytics.debug = False
analytics.write_key = os.environ['SEGMENT_WRITE_KEY']

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'giftlist.views.home', name='home'),
    # url(r'^giftlist/', include('giftlist.foo.urls')),

    url(r'^$', 'Gifts.views.home', name='home'),
    url(r'^signup/(\S+)/$', 'Gifts.views.new_user_signup', name='new_user_signup'),
    url(r'^login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^logout/$', 'Gifts.views.user_logout', name='logout'),

    # Uncomment the admin/doc line below to enable admin documentation:
    #url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^home/', include('Gifts.urls')),
    url(r'^account/', include('password_reset.urls')),
    url(r'^password/', 'django.contrib.auth.views.password_change',
        { 'template_name': 'registration/password_change_form.html' },
        name='password_change'),
    url(r'^password/done/', 'django.contrib.auth.views.password_change_done',
        { 'template_name': 'registration/password_change_done.html' },
        name='password_change_done'),
)

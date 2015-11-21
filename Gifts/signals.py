import analytics
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.auth.signals import user_login_failed
from django.dispatch import receiver
import uuid


# auth completed signal #
@receiver(user_logged_in)
def login_log(sender, **kwargs):
    print "user logged in"
    user = kwargs['user']
    analytics.identify(user.id, {
        'email': user.email,
        'firstName': user.first_name,
        'lastName': user.last_name,
        'username': user.get_username()
    })
    analytics.track(user.id, 'Logged In')


@receiver(user_logged_out)
def logout_log(sender, **kwargs):
    if 'user' in kwargs:
        user = kwargs['user']
        analytics.track(user.id, 'Logged Out')


@receiver(user_login_failed)
def failed_login_log(sender, **kwargs):
    uid = str(uuid.uuid4())  # we don't have access to the request...
    analytics.track(uid, 'Login Failed', kwargs['credentials'])

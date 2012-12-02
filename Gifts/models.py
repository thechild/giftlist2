from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from uuid import uuid4
import os

# this should rarely run
def get_person_from_user(user):
    try:
        # do we already have the user? If so, just return it
        p = Person.objects.get(login_user=user)
    except ObjectDoesNotExist as dne:
        try:
            # now, let's check to see if someone has already added this email address
            p = Person.objects.get(email = user.email)
            p.login_user = user
            p.save()
        except ObjectDoesNotExist as dne:
            # nope, let's create a brand new person
            p = Person()
            p.login_user = user
            p.first_name = user.first_name
            p.last_name = user.last_name
            p.email = user.email
            p.save()
    
    return p

def clear_reserved_gifts(myself, recipient):
    for g in Gift.objects.filter(recipient=recipient).filter(reserved_by=myself):
        g.reserved_by = None
        g.date_reserved = None
        if g.secret:
            g.delete()
        else:
            g.save()

def get_reserved_gifts(myself, recipient):
    selected_gifts = Gift.objects.filter(recipient=recipient).filter(reserved_by=myself)
    return selected_gifts

def make_uuid():
    return str(uuid4())

class Person(models.Model):
    login_user = models.ForeignKey(User, related_name='django user', blank=True, null=True, unique=True, on_delete=models.SET_NULL)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    creation_key = models.CharField(max_length=150, default=make_uuid)
    recipients = models.ManyToManyField("self", symmetrical=False)

    def signup_url(self):
        return '%s%s' % (os.environ.get('BASE_IRI'), reverse('Gifts.views.new_user_signup', args=(self.creation_key,)))

    def gifts(self):
        return Gift.objects.filter(recipient=self).exclude(secret=True)

    def name(self):
        if not (self.first_name and self.last_name):
            return self.email
        else:
            return '%s %s' % (self.first_name, self.last_name)

    def __unicode__(self):
        return self.name()

class Gift(models.Model):
    recipient = models.ForeignKey(Person)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    url = models.URLField(blank=True)
    price = models.CharField(max_length=100, blank=True)
    secret = models.BooleanField(default=False)
    date_added = models.DateTimeField('date created', auto_now_add=True, blank=True)
    reserved_by = models.ForeignKey(Person, related_name='Gift Reservor', blank=True, null=True)
    date_reserved = models.DateTimeField('date reserved', blank=True, null=True)

    def __unicode__(self):
        return '%s (%s)' % (self.title, self.recipient)
from django.shortcuts import render, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from Gifts.models import *
from Gifts.forms import *
from django.template import RequestContext
from datetime import datetime
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.forms import UserCreationForm
from django.core import send_mail

def home(request):
    return HttpResponseRedirect(reverse('Gifts.views.user_home'))

def user_logout(request):
    if request.user.is_authenticated():
        logout(request)
        messages.success(request, "You have been successfully logged out.")
    return HttpResponseRedirect(reverse('django.contrib.auth.views.login'))


def new_user_signup(request, user_key):
    if request.user.is_authenticated():
        logout(request) # can't set up a new account while you're already logged in

    person = get_object_or_404(Person, creation_key__exact=user_key)
    
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            username = form.clean_username()
            password = form.clean_password2()
            form.save()
            user = authenticate(username=username, password=password)
            login(request, user)
            print "Created new user name '%s'" % (form['username'], )
            person.login_user = user
            person.save()
            messages.success(request,"Your account is all set up, and you're now logged in.")
            return HttpResponseRedirect(reverse('Gifts.views.user_home'))
    else:
        try:
            user = User.objects.get(email__exact=person.email)
        except ObjectDoesNotExist as dne:
            user = None

        if user:
            messages.error(request, "You've already created your account.  Please login below.")
            return HttpResponseRedirect(reverse('django.contrib.auth.views.login'))
        else:
            form = UserCreateForm()
            form.initial = {'first_name': person.first_name, 'last_name': person.last_name, 'email': person.email}
        
        return render(request, 'new_user.html',
                {'form': form})

@login_required
def user_home(request):
    myself = get_person_from_user(request.user)
    gifts = Gift.objects.filter(recipient = myself).exclude(secret = True)
    people = Person.objects.all().exclude(pk = myself.pk) # will eventually replace this with something smarter

    people_gifts = {}
    for p in people:
        g = Gift.objects.filter(recipient = p).filter(reserved_by = myself)
        if g.count() > 0:
            people_gifts[p] = g
        else:
            people_gifts[p] = None

    return render(request, "user_home.html", {
        'person' : myself,
        'gifts' : gifts,
        'people_gifts' : people_gifts,
        })

@login_required
def add_gift(request):
    myself = get_person_from_user(request.user)

    if request.method == 'POST':
        form = GiftForm(request.POST)
        if form.is_valid():
            new_gift = form.save(commit=False)
            new_gift.recipient = myself
            new_gift.save()
            return HttpResponseRedirect(reverse('Gifts.views.user_home'))
    else:
        form = GiftForm()

    return render(request, 'add_item.html',
        {'form': form,
        'add_title': 'Add a new gift to your list',
        'add_description': "Enter the details of a gift you would like to receive. Note that you can't change this after you save it, since people will be able to immediately reserve it."})

@login_required
def add_secret_gift(request, recipient_id):
    myself = get_person_from_user(request.user)
    recipient = get_object_or_404(Person, pk=recipient_id)

    if request.method == 'POST':
        form = GiftForm(request.POST)
        if form.is_valid():
            new_gift = form.save(commit=False)
            # clear_reserved_gifts(myself, recipient)
            new_gift.recipient = recipient
            new_gift.secret = True
            new_gift.reserved_by = myself
            new_gift.date_reserved = datetime.now()
            new_gift.save()
            return HttpResponseRedirect(reverse('Gifts.views.view_user', args=(recipient.pk,)))
    else:
        form = GiftForm()

    return render(request, 'add_item.html',
        {'form': form,
        'add_title': 'Add a new gift for %s' % recipient.name(),
        'add_description': 'Enter the details of the gift you would like to get for %s.  No one besides you will ever see this information.' % recipient.name()})

@login_required
def add_person(request):
    myself = get_person_from_user(request.user)

    if request.method == 'POST':
        form = PersonForm(request.POST)
        if form.is_valid():
            new_person = form.save()
            # form a relationship eventually, or maybe send an email, etc
            # send an email letting them know how to sign up:

            email_subject = "You've been invited to Gift Exchange!"
            email_body = "Your friend %s has invited you to share gift lists on Gift Exchange, a simple service Chris Child put together for this Christmas.  Click this link to learn more and sign up:\n%s" % (myself.name(), new_person.signup_url())
            send_mail(email_subject, email_body, 'thechild+giftexchange@gmail.com', [new_person.email, 'thechild+giftexchange@gmail.com'], fail_silently=True)
            return HttpResponseRedirect(reverse('Gifts.views.user_home'))
    else:
        form = PersonForm()

    return render(request,'add_item.html',
        {'form': form,
        'add_title': 'Add a new person you would like to give a gift to.',
        'add_description': "By adding a new person, you can track what gift you'd like to give them."})

@login_required
def remove_gift(request, gift_id):
    myself = get_person_from_user(request.user)
    gift = get_object_or_404(Gift, pk=gift_id)

    if gift.recipient == myself and not gift.secret:
        if request.method == 'POST':
            # this is the confirmation
            title = gift.title
            gift.delete()
            messages.info(request, "The %s was removed from your gift list." % title)
        else:
            return render(request, 'confirm_delete.html', {
                'gift': gift,
                })
    else:
        messages.error(request, "You tried to delete a gift that isn't yours!")

    return HttpResponseRedirect(reverse('Gifts.views.user_home'))

@login_required
def reserve_gift(request, recipient_id, gift_id):
    myself = get_person_from_user(request.user)
    recipient = get_object_or_404(Person, pk=recipient_id)
    gift = get_object_or_404(Gift, pk=gift_id)

    if gift.reserved_by is None:
        # unreserve any other gifts first
        # clear_reserved_gifts(myself, recipient)
        # then reserve this gift for me
        gift.reserved_by = myself
        gift.date_reserved = datetime.now()
        gift.save()
        messages.success(request, "You've successfully reserved the %s for %s!" % (gift.title, recipient.first_name))
    else:
        messages.error(request, 'Someone has already reserved that gift!')

    return HttpResponseRedirect(reverse('Gifts.views.view_user', args=(recipient.pk,)))

@login_required
def unreserve_gift(request, recipient_id, gift_id):
    myself = get_person_from_user(request.user)
    recipient = get_object_or_404(Person, pk=recipient_id)
    gift = get_object_or_404(Gift, pk=gift_id)

    if gift.reserved_by == myself and gift.recipient == recipient:
        gift.reserved_by = None
        gift.date_reserved = None
        if gift.secret:
            gift.delete()
        else:
            gift.save()
        messages.success(request, "You are no longer reserving the %s for %s." % (gift.title, recipient.first_name))
    else:
        messages.error(request, "You don't have permission to access that gift!")

    return HttpResponseRedirect(reverse('Gifts.views.view_user', args=(recipient.pk,)))

@login_required
def view_user(request, user_id):
    myself = get_person_from_user(request.user)
    user = get_object_or_404(Person, pk=user_id)
    reserved_gifts = [g.pk for g in get_reserved_gifts(myself, user)]

    gifts = Gift.objects.filter(recipient=user).filter(Q(secret=False) | Q(pk__in=reserved_gifts)) # may want a way to put things in without reserving them...

    return render(request, 'view_user.html',{
        'user' : user,
        'reserved_gifts' : reserved_gifts,
        'gifts' : gifts,
        })
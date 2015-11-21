from django.shortcuts import render, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from Gifts.models import *
from Gifts.forms import *
from datetime import datetime
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from Gifts.helpers import send_signup_email, convert_link, send_all_update_emails, send_request_email
import analytics


# / redirects to the user_home view #
def home(request):
    return HttpResponseRedirect(reverse('Gifts.views.user_home'))


def user_logout(request):
    if request.user.is_authenticated():
        logout(request)

        messages.success(request, "You have been successfully logged out.")
    return HttpResponseRedirect(reverse('django.contrib.auth.views.login'))


def new_user_signup(request, user_key):
    if request.user.is_authenticated():
        logout(request)  # can't set up a new account while you're already logged in
    if user_key == 'test':
        person = Person()
    else:
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
            analytics.track(user.id, 'Signup')
            messages.success(request, "Your account is all set up, and you're now logged in as '%s'." % user.username)
            return HttpResponseRedirect(reverse('Gifts.views.user_home'))
    else:
        try:
            user = User.objects.get(email__exact=person.email)
        except ObjectDoesNotExist:
            user = None

        if user:
            messages.error(request, ("You've already created your account.  Please login below.  "
                                     "Your user name is '{{ user.username }}'."))
            return HttpResponseRedirect(reverse('django.contrib.auth.views.login'))
        else:
            form = UserCreateForm()
            form.initial = {'first_name': person.first_name, 'last_name': person.last_name, 'email': person.email}

    return render(request, 'new_user.html', {'form': form})


@login_required
def user_home(request):
    myself = get_person_from_user(request.user)
    gifts = Gift.objects.filter(recipient=myself).exclude(secret=True)
    # people = Person.objects.all().exclude(pk = myself.pk) # will eventually replace this with something smarter
    people = myself.recipients.all()

    people_gifts = {}
    for p in people:
        g = Gift.objects.filter(recipient=p).filter(reserved_by=myself)
        if g.count() > 0:
            people_gifts[p] = g
        else:
            people_gifts[p] = None

    analytics.page(request.user.id, 'giftlist', 'user_home')

    return render(request, "user_home.html", {
        'person': myself,
        'gifts': gifts,
        'people_gifts': people_gifts,
        })


@login_required
def add_gift(request, gift_id=None):
    myself = get_person_from_user(request.user)
    if gift_id:
        gift = get_object_or_404(Gift, pk=gift_id)
        if gift.recipient != myself:
            messages.error(request, "You don't have permission to edit that gift.")
            return HttpResponseRedirect(reverse('Gifts.views.user_home'))
    else:
        gift = None

    if request.method == 'POST':
        form = GiftForm(request.POST, instance=gift)
        if form.is_valid():
            new_gift = form.save(commit=False)
            new_gift.recipient = myself
            if new_gift.url:
                new_gift.url = convert_link(new_gift.url)
            if not new_gift.pk:
                send_all_update_emails(myself)  # this probably needs to somehow be a worker or it might get slow

                analytics.track(request.user.id, 'Added a Gift', {
                    'title': new_gift.title,
                    'url': new_gift.url,
                    'type': 'self'
                    })

                new_gift.save()
            else:
                analytics.track(request.user.id, 'Edited a Gift', {
                    'gift_id': new_gift.pk,
                    'title': new_gift.title,
                    'url': new_gift.url,
                    'type': 'self'
                    })

            return HttpResponseRedirect(reverse('Gifts.views.user_home'))
    else:
        analytics.page(request.user.id, 'giftlist', 'add_gift')
        form = GiftForm(instance=gift)

    if gift_id:
        add_title = 'Edit the gift that you want to receive.'
        submit_text = 'Change'
    else:
        add_title = 'Add a new gift to your list.'
        submit_text = 'Add'

    add_description = ("Enter the details of a gift you would like to receive. "
                       "Note that you can't change this after you save it, since people will be able to immediately reserve it.")

    return render(request, 'add_item.html',
                  {'form': form,
                   'add_title': add_title,
                   'add_description': add_description,
                   'submit_text': submit_text,
                   'giftid': gift_id })


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
            if new_gift.url:
                new_gift.url = convert_link(new_gift.url)
            if not new_gift.pk:
                analytics.track(request.user.id, 'Added a Gift', {
                    'title': new_gift.title,
                    'url': new_gift.url,
                    'type': 'secret'
                    })
            else:
                analytics.track(request.user.id, 'Edited a Gift', {
                    'gift_id': new_gift.pk,
                    'title': new_gift.title,
                    'url': new_gift.url,
                    'type': 'secret'
                    })
            new_gift.save()
            return HttpResponseRedirect(reverse('Gifts.views.view_user', args=(recipient.pk,)))
    else:
        analytics.page(request.user.id, 'giftlist', 'add_secret_gift')
        form = GiftForm()

    return render(request, 'add_item.html',
                  {'form': form,
                   'add_title': 'Add a new gift for %s' % recipient.name(),
                   'add_description': ('Enter the details of the gift you would like to get for %s.  '
                                       'No one besides you will ever see this information.' % recipient.name())
                   })


@login_required
def remove_gift(request, gift_id):
    myself = get_person_from_user(request.user)
    gift = get_object_or_404(Gift, pk=gift_id)

    if gift.recipient == myself and not gift.secret:
        if request.method == 'POST':
            # this is the confirmation
            title = gift.title
            analytics.track(request.user.id, 'Deleted a Gift', {
                'gift_id': gift.id,
                'title': gift.title,
                'url': gift.url
                })
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

    success = false

    if gift.reserved_by is None:
        # unreserve any other gifts first
        # clear_reserved_gifts(myself, recipient)
        # then reserve this gift for me
        gift.reserved_by = myself
        gift.date_reserved = datetime.now()
        gift.save()
        messages.success(request, "You've successfully reserved the %s for %s!" % (gift.title, recipient.first_name))
        success = true
    else:
        messages.error(request, 'Someone has already reserved that gift!')

    analytics.track(request.user.id, 'Reserved a Gift', {
        'gift_title': gift.title,
        'recipient_id': recipient.id,
        'recipient_name': recipient.name(),
        'success': 'Yes' if success else 'No'
        })

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

        analytics.track(request.user.id, 'Unreserved a Gift', {
            'gift_title': gift.title,
            'recipient_id': recipient.id,
            'recipient_name': recipient.name()
            })
    else:
        messages.error(request, "You don't have permission to access that gift!")

    return HttpResponseRedirect(reverse('Gifts.views.view_user', args=(recipient.pk,)))


@login_required
def user_gift_request(request, user_id):
    myself = get_person_from_user(request.user)
    user = get_object_or_404(Person, pk=user_id)
    send_request_email(myself, user)
    messages.success(request, ("An email has been sent to %s asking them to add more gifts.  "
                               "We'll let you know when they do." % user.name()))
    analytics.track(request.user.id, 'Requested more Gifts', {
        'recipient_id': user.id,
        'recipient_name': user.name()
        })
    return HttpResponseRedirect(reverse('Gifts.views.view_user', args=(user.pk,)))


@login_required
def view_user(request, user_id):
    myself = get_person_from_user(request.user)
    user = get_object_or_404(Person, pk=user_id)
    reserved_gifts = [g.pk for g in get_reserved_gifts(myself, user)]

    gifts = Gift.objects.filter(recipient=user).filter(Q(secret=False) | Q(pk__in=reserved_gifts))
    unreserved_gift_count = gifts.exclude(reserved_by__isnull=True).count()

    analytics.page(request.user.id, 'giftlist', 'view_user', {
        'recipient_id': user.id,
        'recipient_name': user.name(),
        'reserved_gifts': len(reserved_gifts),
        'available_gifts': unreserved_gift_count
        })

    return render(request, 'view_user.html', {
        'user': user,
        'reserved_gifts': reserved_gifts,
        'gifts': gifts,
        })


#####################################
#### Following and Adding People ####
#####################################

@login_required
def add_person(request):
    myself = get_person_from_user(request.user)

    if request.method == 'POST':
        form = PersonForm(request.POST)
        if form.is_valid():
            new_person = form.save()
            new_person.invited_by = myself.login_user
            new_person.save()
            myself.recipients.add(new_person)
            new_person.recipients.add(myself)  # let's start them off with one person on their list
            # send an email letting them know how to sign up:
            send_signup_email(myself, new_person)
            analytics.track(request.user.id, 'Invited a new Person', {
                'person_id': new_person.id
                })
            return HttpResponseRedirect(reverse('Gifts.views.view_all_people'))
    else:
        form = PersonForm()

    analytics.page(request.user.id, 'giftlist', 'add_person')
    return render(request, 'add_item.html',
                  {'form': form,
                   'add_title': 'Add a new person you would like to give a gift to.',
                   'add_description': ("By adding a new person, you can track what gift you'd like to give them.  "
                                       "This will also send them an email inviting them to join Gift Exchange "
                                       "so that you can see the gifts they want.")})


@login_required
def view_all_people(request):
    myself = get_person_from_user(request.user)
    all_people = Person.objects.exclude(pk=myself.pk).order_by('first_name', 'last_name')

    q = ''

    if 'q' in request.GET:
        q = request.GET['q']
        qfn, s, qln = q.rpartition(' ')
        if qfn:
            all_people = all_people.filter(
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q) |
                (Q(first_name__icontains=qfn) &
                 Q(last_name__icontains=qln)) |
                Q(email__icontains=q))
        else:
            all_people = all_people.filter(Q(first_name__icontains=q)
                                           | Q(last_name__icontains=q)
                                           | Q(email__icontains=q))

    people = []
    for person in all_people:
        people.append((person, myself.recipients.filter(pk=person.pk).count() > 0))

    analytics.page(request.user.id, 'giftlist', 'view_people', {
        'count': len(people),
        'filtered': 'Yes' if 'q' in request.GET else 'No'
        })

    return render(request, 'view_all_people.html', {'myself': myself, 'people': people, 'q': q})


@login_required
def follow_person(request, person_id):
    myself = get_person_from_user(request.user)
    person = get_object_or_404(Person, pk=person_id)
    if myself.recipients.filter(pk=person.pk).count() > 0:
        messages.warning(request, "You've already added %s to your gift list!" % person.name())
    else:
        myself.recipients.add(person)
        messages.success(request, "%s is now on your gift list! Pick them out something nice!" % person.name())
        analytics.track(request.user.id, 'Followed a Person', {
            'recipient_id': person.id,
            'total_recipients': myself.recipients.count()
            })
    return HttpResponseRedirect(reverse('Gifts.views.view_all_people'))


@login_required
def unfollow_person(request, person_id):
    myself = get_person_from_user(request.user)
    person = get_object_or_404(Person, pk=person_id)
    if myself.recipients.filter(pk=person.pk).count() > 0:
        myself.recipients.remove(person)
        cleared_gifts = clear_reserved_gifts(myself, person)
        messages.success(request,
                         ("Removed %s from your list, and unreserved %s "
                          "gifts you had reserved for them.") % (person.name(), len(cleared_gifts)))
        analytics.track(request.user.id, 'Unfollowed a Person', {
            'recipient_id': person.id,
            'total_recipients': myself.recipients.count()
            })
    else:
        messages.warning(request, "You weren't following %s." % person.name())
    return HttpResponseRedirect(reverse('Gifts.views.view_all_people'))


@login_required
def manage_account(request):
    # myself = get_person_from_user(request.user)
    analytics.page(request.user.id, 'giftlist', 'manage_account')
    messages.warning(request, "Sorry, this isn't implemented yet.")
    return HttpResponseRedirect(reverse('Gifts.views.user_home'))

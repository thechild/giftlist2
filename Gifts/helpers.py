from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from giftlist.settings import AMAZON_AFFILIATE_TAG
from amazonify import amazonify
from urlparse import urlparse
from django.core.urlresolvers import reverse
from Gifts.models import PersonEmail
import datetime
import os

## email helper function ##
def render_and_send_email(sender, recipient, subject, msg_type, link=''):
    from_email = sender.email
    to_email = [recipient.email, ]
    
    TEMPLATES = {
        PersonEmail.GIFT_ADDED_EMAIL: 'emails/update_email.txt',
        PersonEmail.REQUEST_EMAIL: 'emails/request_email.txt',
        PersonEmail.SIGNUP_EMAIL: 'emails/new_user_email.txt'
        }

    plaintext = get_template(TEMPLATES[msg_type])
    c = Context({
        'recipient': recipient,
        'sender': sender,
        'link': link
        })
    text_content = plaintext.render(c)
    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    try:
        if os.environ['SEND_EMAILS'] == "True":
            msg.send()
            print "Email Sent"
    except KeyError:
        print "SEND_MESSAGES is false, so not sending this message:\n"
        print "From: '%s'\tTo: '%s'\tSubject: '%s'" % (from_email, to_email, subject)
        print "%s" % text_content

    stored_email = PersonEmail(sender=sender,
        recipient=recipient,
        subject=subject,
        text_body=text_content,
        type_of_email=msg_type)
    stored_email.save()
    stored_email.date_sent = stored_email.date_published # this is in case we later want to publish and send at different times
    stored_email.save()

## sends a signup email to recipient on behalf of sender ##
def send_signup_email(sender, recipient):
    subject = "What do you want for the holidays?"
    render_and_send_email(sender, recipient, subject, PersonEmail.SIGNUP_EMAIL, recipient.signup_url())

## sends an email to recipient requesting he/she add more gifts on behalf of sender ##
def send_request_email(sender, recipient):
    subject = "Please add some gifts on Gift List!"
    # only let you send one a day - maybe should even make this a longer interval?
    # also note that this currently fails silently, telling the user an email was sent even if we didn't re-send
    sent_messages = PersonEmail.objects.filter(sender=sender, recipient=recipient, type_of_email__exact=PersonEmail.REQUEST_EMAIL).order_by('-date_sent')
    print "sent_messages in send_request_email: %s" % sent_messages
    if sent_messages.count() == 0 or sent_messages[0].date_sent.date() < datetime.date.today():
        link = '%s%s' % (os.environ.get('BASE_IRI'), reverse('Gifts.views.user_home', None))
        render_and_send_email(sender, recipient, subject, PersonEmail.REQUEST_EMAIL, link)

## sends an email to recipient letting him/her know that sender has added new gifts.  Sends a maximum of once a day ##
def send_update_email(sender, recipient):
    # see if one's already been sent:
    sent_messages = PersonEmail.objects.filter(sender=sender, recipient=recipient, type_of_email__exact=PersonEmail.GIFT_ADDED_EMAIL).order_by('-date_sent')
    if sent_messages.count() == 0 or sent_messages[0].date_sent.date() < datetime.date.today():
        # we haven't sent a message today, so let's send one.
        subject = "I've added some gifts on Gift List"
        link = '%s%s' % (os.environ.get('BASE_IRI'), reverse('Gifts.views.view_user', args=[sender.pk]))
        render_and_send_email(sender, recipient, subject, PersonEmail.GIFT_ADDED_EMAIL, link)
    else:
        print "A message was sent recently from %s to %s so we won't send another." % (sender, recipient)

def send_all_update_emails(sender):
    recipients = Person.objects.filter(recipients=sender)
    for recipient in receipients:
        send_update_email(sender, recipient)

def clear_reserved_gifts(sender, recipient):
    gifts = Gift.objects.filter(recipient=recipient.pk, reserved_by=sender.pk)
    for g in gifts:
        g.reserved_by = None
        g.date_reserved = None
    return gifts.count()

def convert_link(link):
    new_link = None

    if "amazon." in urlparse(link).hostname:
        new_link = amazonify(link, AMAZON_AFFILIATE_TAG)

    if new_link:
        return new_link
    else:
        return link
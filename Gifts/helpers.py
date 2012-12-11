from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from giftlist.settings import AMAZON_AFFILIATE_TAG
from amazonify import amazonify
from urlparse import urlparse
from django.core.urlresolvers import reverse
from Gifts.models import PersonEmail
import os

## email helper function ##
def render_and_send_email(sender, recipient, subject, template, link=''):
    from_email = sender.email
    to_email = [recipient.email, ]
    plaintext = get_template(template)
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
    except KeyError:
        print "SEND_MESSAGES is false, so not sending this message:\n"
        print "From: '%s'\tTo: '%s'\tSubject: '%s'" % (from_email, to_email, subject)
        print "%s" % text_content

    stored_email = PersonEmail(sender=sender, recipient=recipient, subject=subject, text_body=text_content)
    if template == 'emails/update_email.txt':
        stored_email.type_of_email = PersonEmail.GIFT_ADDED_EMAIL
    elif template == 'emails/new_user_email.txt':
        stored_email.type_of_email = PersonEmail.SIGNUP_EMAIL
    elif template == 'emails/request_gifts.txt':
        stored_email.type_of_email = PersonEmail.REQUEST_EMAIL
    stored_email.save()

## sends a signup email to recipient on behalf of sender ##
def send_signup_email(sender, recipient):
    subject = "What do you want for the holidays?"
    render_and_send_email(sender, recipient, subject, 'emails/new_user_email.txt', recipient.signup_url())

## sends an email to recipient requesting he/she add more gifts on behalf of sender ##
def send_request_email(sender, recipient):
    subject = "Please add some gifts on Gift List!"
    link = reverse('Gifts.views.user_home', None)
    render_and_send_email(sender, recipient, subject, 'emails/request_email.txt', link)

## sends an email to recipient letting him/her know that sender has added new gifts.  Sends a maximum of once a day ##
def send_update_email(sender, recipient):
    # see if one's already been sent:
    sent_messages = PersonEmail.objects.filter(sender=sender, recipient=recipient, type_of_email__exact=PersonEmail.GIFT_ADDED_EMAIL).order_by('-sent_date')
    if sent_messages.count() > 0 and sent_messages[0].sent_date.date() < datetime.date():
        # we haven't sent a message today, so let's send one.
        subject = "I've added some gifts on Gift List"
        link = reverse('Gifts.views.view_user', args=[sender.pk])
        render_and_send_email(sender, recipient, subject, 'emails/update_email.txt', link)

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
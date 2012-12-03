from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from giftlist.settings import SEND_UPDATE_EMAILS, SEND_SIGNUP_EMAILS, AMAZON_AFFILIATE_TAG
from amazonify import amazonify
from urlparse import urlparse

def send_signup_email(sender, recipient):
    if SEND_SIGNUP_EMAILS:
        subject = "What do you want for the holidays?"
        from_email = sender.email
        to_email = [recipient.email, 'thechild+giftexchange@gmail.com']
        
        plaintext = get_template('emails/new_user_email.txt')
        #htmly = get_template('new_user_email.html')
        
        c = Context({
            'recipient': recipient,
            'sender': sender,
            })

        text_content = plaintext.render(c)
        #html_content = htmly.render(c)

        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        #msg.attach_alternative(html_content, "text/html")
        msg.send() #maybe run this all in a worker?

def send_request_email(sender, recipient):
    if SEND_REQUEST_EMAILS:
        subject = "Please add some gifts on Gift List!"
        from_email = sender.email
        to_email = [recipient.email, ]

        plaintext = get_template('emails/request_email.txt')

        c = Context({
            'recipient': recipient,
            'sender': sender,
            })

        text_content = plaintext.render(c)

        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.send()

def send_update_email(sender, recipient):
    if SEND_UPDATE_EMAILS:
        subject = "I've added some gifts on Gift List"
        from_email = sender.email
        to_email = [recipient.email, ]

        plaintext = get_template('emails/update_email.txt')

        c = Context({
            'recipient': recipient,
            'sender': sender,
            'link': reverse('Gifts.views.view_user', recipient.pk)
            })

        text_content = plaintext.render(c)

        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.send() #maybe run this all in a worker?

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
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context

def send_signup_email(sender, recipient):
    subject = "Join me on Gift Exchange"
    from_email = sender.email
    to_email = [recipient.email, 'thechild+giftexchange@gmail.com']
    
    plaintext = get_template('new_user_email.txt')
    #htmly = get_template('new_user_email.html')
    
    c = Context({
        'recipient': recipient,
        'sender': sender,
        })

    text_content = plaintext.render(c)
    #html_content = htmly.render(c)

    msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
    #msg.attach_alternative(html_content, "text/html")
    msg.send()
from Gifts.models import Gift, Person, PersonEmail
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin


class GiftAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'secret', 'reserved_by')
    list_filter = ('recipient', 'reserved_by')


def requested_gift_count(obj):
    return Gift.objects.filter(recipient=obj).filter(secret=False).count()


def reserved_gift_count(obj):
    return Gift.objects.filter(recipient=obj).filter(reserved_by__isnull=False).count()


def has_account(obj):
    if obj.login_user:
        return True
    else:
        return False


class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', requested_gift_count, reserved_gift_count, has_account)


class MyUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('date_joined',)


class PersonEmailAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'sender', 'subject', 'type_of_email', 'date_sent')
    date_hierarchy = 'date_sent'
    list_display_links = ('recipient', 'sender')
    list_filter = ('type_of_email', 'date_sent')
    search_fields = ['recipient__first_name', 'recipient__last_name', 'recipient__email',
                     'sender__first_name', 'sender__last_name', 'sender__email']
    ordering = ('-date_sent',)

admin.site.register(PersonEmail, PersonEmailAdmin)
admin.site.register(Gift, GiftAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)

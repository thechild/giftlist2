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

class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', requested_gift_count, reserved_gift_count)

class MyUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('date_joined',)

class PersonEmailAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'sender', 'subject', 'type_of_email', 'date_sent')
    date_hierarchy = 'date_sent'
    list_display_links = ('recipient', 'sender')
    list_filter = ('recipient', 'sender', 'type_of_email', 'date_sent')
    ordering = ('-date_sent',)

admin.site.register(PersonEmail, PersonEmailAdmin)
admin.site.register(Gift, GiftAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)

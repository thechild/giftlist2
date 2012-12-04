from Gifts.models import Gift, Person
from django.contrib import admin
from django.contrib.auth import User
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
    list_display = UserAdmin.list_display + ('date_joined')

admin.site.register(Gift, GiftAdmin)
admin.site.register(Person, PersonAdmin)
admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)
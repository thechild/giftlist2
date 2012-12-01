from Gifts.models import Gift, Person
from django.contrib import admin

class GiftAdmin(admin.ModelAdmin):
    list_display = ('title', 'recipient', 'secret', 'reserved_by')
    list_filter = ('recipient', 'reserved_by')

def requested_gift_count(obj):
    return Gift.objects.filter(recipient=obj).filter(secret=False).count()

def reserved_gift_count(obj):
    return Gift.objects.filter(recipient=obj).filter(reserved_by__isnull=False).count()

class PersonAdmin(admin.ModelAdmin):
    list_display = ('name', requested_gift_count, reserved_gift_count)

admin.site.register(Gift, GiftAdmin)
admin.site.register(Person, PersonAdmin)
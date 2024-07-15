from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Subscriptions


class SubscriptionsAdmin(admin.ModelAdmin):
    display = (
        "user",
        "following",
    )
    list_filter = ("user",)


class SubscriptionsInline(admin.StackedInline):
    model = Subscriptions
    extra = 1
    fk_name = "user"


class CustomUserAdmin(UserAdmin):
    inlines = (SubscriptionsInline,)
    display = ("email", "id", "username", "first_name", "last_name")
    search_fields = ("email", "username")
    list_filter = ("username",)
    list_display_links = ("email", "username")


admin.site.register(User, CustomUserAdmin)
admin.site.register(Subscriptions, SubscriptionsAdmin)

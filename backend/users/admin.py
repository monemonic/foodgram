from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


class CustomUserAdmin(UserAdmin):
    list_display = (
        'email',
        'id',
        'username',
        'first_name',
        'last_name'

    )
    search_fields = ('email', 'id', 'username')
    list_filter = ('username',)
    list_display_links = ('username',)


admin.site.register(User, CustomUserAdmin)

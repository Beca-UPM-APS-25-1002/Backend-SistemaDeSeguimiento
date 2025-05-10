from django.contrib import admin
from solo.admin import SingletonModelAdmin
from .models import EmailSettings


admin.site.register(EmailSettings, SingletonModelAdmin)

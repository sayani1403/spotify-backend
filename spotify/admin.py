from django.contrib import admin

from .models import User, Artist, Song, Rating


admin.site.register(User)
admin.site.register(Artist)
admin.site.register(Song)
admin.site.register(Rating)

from django.contrib import admin

from tests.testapp.models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    search_fields = ["title", "isbn", "author__name"]
    list_display = ["title", "author"]

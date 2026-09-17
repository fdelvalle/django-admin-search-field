from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        app_label = "testapp"

    def __str__(self):
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=200)
    isbn = models.CharField("ISBN", max_length=20)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name="books")

    class Meta:
        app_label = "testapp"

    def __str__(self):
        return self.title

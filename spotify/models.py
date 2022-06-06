from django.db import models


class User(models.Model):
    name = models.CharField(max_length=20, unique=True)
    email = models.EmailField(max_length=256, unique=True)

    def __str__(self):
        return self.name


class Artist(models.Model):
    name = models.CharField(max_length=20)
    dob = models.DateField()
    bio = models.TextField()
    rating_sum = models.FloatField(default=0)
    rating_count = models.BigIntegerField(default=0)

    def avg_rating(self):
        if self.rating_count > 0:
            return self.rating_sum / self.rating_count

    def __str__(self):
        return self.name


class Song(models.Model):
    name = models.CharField(max_length=20)
    dor = models.DateField()
    cover = models.ImageField(upload_to='covers/', null=True, blank=True)
    rating_sum = models.FloatField(default=0)
    rating_count = models.BigIntegerField(default=0)
    artists = models.ManyToManyField(Artist)

    def avg_rating(self):
        if self.rating_count > 0:
            return self.rating_sum / self.rating_count

    def __str__(self):
        return self.name


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    rating = models.SmallIntegerField()  # TODO: Add validator

    class Meta:
        unique_together = ('user', 'song')

    def __str__(self):
        return f"{self.user} -> {self.song} -> {self.rating}"

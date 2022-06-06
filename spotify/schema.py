from django.db.models import Sum, F
from django.core.exceptions import ValidationError
import graphene
from graphene_django import DjangoObjectType
from .models import User, Artist, Song, Rating
from django.db import transaction


class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ('id','name')


class ArtistType(DjangoObjectType):
    class Meta:
        model = Artist
        fields = (
            'id',
            'name',
            'dob',
            'bio',
            'rating_count',
        )

    avg_rating = graphene.Float()

    def resolve_avg_rating(self, info):
        return self.avg_rating()

class SongType(DjangoObjectType):
    class Meta:
        model = Song
        fields = (
            'id',
            'name',
            'dor',
            'cover',
            'artists',
            'rating_count',
        )

    avg_rating = graphene.Float()

    def resolve_avg_rating(self, info):
        return self.avg_rating()


class ArtistInput(graphene.InputObjectType):
    name = graphene.String()
    dob = graphene.Date()
    bio = graphene.String()


class CreateArtist(graphene.Mutation):
    class Arguments:
        input = ArtistInput(required=True)

    artist = graphene.Field(ArtistType)

    @classmethod
    def mutate(cls, root, info, input):
        artist = Artist(
            name=input.name,
            dob=input.dob,
            bio=input.bio,
        )
        artist.save()
        return CreateArtist(artist=artist)


class SongInput(graphene.InputObjectType):
    name = graphene.String()
    dor = graphene.Date()
    cover = graphene.String()
    artists = graphene.List(graphene.Int)


class CreateSong(graphene.Mutation):
    class Arguments:
        input = SongInput(required=True)

    song = graphene.Field(SongType)

    @classmethod
    def mutate(cls, root, info, input):
        song = Song(
            name=input.name,
            dor=input.dor,
        )
        song.save()
        song.artists.add(*input.artists)
        song.save()
        return CreateSong(song=song)


class RatingInput(graphene.InputObjectType):
    user_id = graphene.Int()
    song_id = graphene.Int()
    rating = graphene.Float()


class RatingType(DjangoObjectType):
    class Meta:
        model = Rating
        fields = (
            'user',
            'song',
            'rating',
        )


class RateSong(graphene.Mutation):
    class Arguments:
        input = RatingInput(required=True)

    rating = graphene.Field(RatingType)

    @classmethod
    def mutate(cls, root, info, input):
        if input.rating is not None and (input.rating < 1 or input.rating > 5):
            raise ValidationError("Invalid rating")
        with transaction.atomic():
            try:
                rating = Rating.objects.get(user__id=input.user_id, song=input.song_id)
            except Rating.DoesNotExist:
                song = Song.objects.get(id=input.song_id)
                rating = Rating(
                    user=User.objects.get(id=input.user_id),
                    song=song,
                    rating=input.rating,
                )
                rating.save()

                ratings = Rating.objects.filter(song=song)
                song.rating_sum = ratings.aggregate(Sum('rating'))['rating__sum']
                song.rating_count = ratings.count()
                song.save()

                for artist in song.artists.all():
                    sums = artist.song_set.aggregate(Sum('rating_sum'), Sum('rating_count'))
                    artist.rating_sum = sums['rating_sum__sum']
                    artist.rating_count = sums['rating_count__sum']
                    artist.save()
            else:
                if input.rating:
                    rating.rating = input.rating
                    rating.save()
                    ratings = Rating.objects.filter(song=rating.song)
                    rating.song.rating_sum = ratings.aggregate(Sum('rating'))['rating__sum']
                    rating.song.save()
                    for artist in rating.song.artists.all():
                        sums = artist.song_set.aggregate(Sum('rating_sum'))
                        artist.rating_sum = sums['rating_sum__sum']
                        artist.save()
                else:
                    rating.song.rating_sum -= rating.rating
                    rating.song.rating_count -= 1
                    rating.song.save()
                    rating.song.artists.update(
                        rating_sum=F('rating_sum') - rating.rating,
                        rating_count=F('rating_count') - 1,
                    )
                    rating.delete()

        return RateSong(rating=rating)


class Query(graphene.ObjectType):
    users = graphene.List(UserType)
    songs = graphene.List(SongType)
    artists = graphene.List(ArtistType)

    def resolve_artists(root, info, **kwargs):
        # Querying a list
        return sorted(Artist.objects.all(), key=lambda x: x.avg_rating() or 0, reverse=True)[:10]

    def resolve_songs(root, info, **kwargs):
        # Querying a list
        return sorted(Song.objects.all(), key=lambda x: x.avg_rating() or 0, reverse=True)[:10]

    def resolve_users(root, info, **kwargs):
        return User.objects.all()


class Mutation(graphene.ObjectType):
    create_artist = CreateArtist.Field()
    create_song = CreateSong.Field()
    rate_song = RateSong.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)

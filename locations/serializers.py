from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Category, Location

User = get_user_model()


class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username")


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "description", "created_at")
        read_only_fields = ("id", "created_at")


class LocationSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True) 
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Location
        fields = (
            "id",
            "title",
            "description",
            "category",
            "category_name",
            "address",
            "latitude",
            "longitude",
            "author",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "author", "created_at", "updated_at")
        extra_kwargs = {
            "latitude": {"coerce_to_string": False},
            "longitude": {"coerce_to_string": False},
        }
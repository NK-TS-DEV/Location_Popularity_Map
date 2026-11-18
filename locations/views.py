from django.db.models import ProtectedError, Avg, Count, FloatField, ExpressionWrapper, F
from django.db.models.functions import Coalesce
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from .filters import LocationFilter
from .models import Category, Location
from .permissions import IsAdminOrReadOnly, IsOwnerOrAdminOrReadOnly
from .serializers import CategorySerializer, LocationSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"detail": "Category is used by locations and cannot be deleted."},
                status=status.HTTP_409_CONFLICT,
            )


class LocationViewSet(viewsets.ModelViewSet):
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdminOrReadOnly]

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]

    filterset_class = LocationFilter

    search_fields = ["title", "description"]

    ordering_fields = ["created_at", "rating", "popularity"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Location.objects.filter(
            is_deleted=False).select_related(
            "author",
            "category").annotate(
            rating=Coalesce(
                Avg("reviews__rating"),
                0.0,
                output_field=FloatField()),
            reviews_count=Count(
                "reviews",
                distinct=True),
            popularity=ExpressionWrapper(
                F("rating")
                * 2.0
                + F("reviews_count")
                * 1.5,
                output_field=FloatField()))

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

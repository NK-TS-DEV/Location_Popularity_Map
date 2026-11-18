# reviews/views.py
from django.db.models import Count, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Review, ReviewVote
from .serializers import ReviewSerializer, ReviewVoteSerializer


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Дозвіл на редагування/видалення тільки для автора або адміна."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user or request.user.is_staff


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["location", "author", "rating"]

    def get_queryset(self):
        # Захист для генерації схеми Swagger
        if getattr(self, 'swagger_fake_view', False):
            return Review.objects.none()

        return Review.objects.select_related("author", "location").annotate(
            likes_count=Count("votes", filter=Q(votes__value=1)),
            dislikes_count=Count("votes", filter=Q(votes__value=-1)),
        )

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[permissions.IsAuthenticated],
        serializer_class=ReviewVoteSerializer,
    )
    def vote(self, request, pk=None):
        review = self.get_object()
        serializer = ReviewVoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        value = serializer.validated_data["value"]

        vote, created = ReviewVote.objects.update_or_create(
            review=review,
            user=request.user,
            defaults={"value": value},
        )

        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(
            {"detail": "Голос успішно зараховано.", "value": vote.value},
            status=status_code,
        )

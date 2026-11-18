from rest_framework import serializers
from .models import Review, ReviewVote


class ReviewSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    dislikes_count = serializers.IntegerField(read_only=True)
    user_vote = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = (
            "id",
            "location",
            "author",
            "rating",
            "comment",
            "created_at",
            "updated_at",
            "likes_count",
            "dislikes_count",
            "user_vote",
        )
        read_only_fields = ("id", "author", "created_at", "updated_at")

    def get_user_vote(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            vote = obj.votes.filter(user=request.user).first()
            return vote.value if vote else None
        return None

    def validate(self, attrs):
        request = self.context.get("request")
        if request and request.method == "POST":
            location = attrs.get("location")
            if Review.objects.filter(location=location, author=request.user).exists():
                raise serializers.ValidationError(
                    {"detail": "Ви вже залишили відгук до цієї локації."}
                )
        return attrs

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        return super().create(validated_data)


class ReviewVoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewVote
        fields = ("id", "value", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_value(self, value):
        if value not in [ReviewVote.LIKE, ReviewVote.DISLIKE]:
            raise serializers.ValidationError("Значення повинно бути 1 (Like) або -1 (Dislike).")
        return value
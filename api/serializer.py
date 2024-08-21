from rest_framework import serializers
from .models import Traject, Plan, User, Match, Guider,Transport,Train


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance


class TrajectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Traject
        fields = "__all__"

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = "__all__"


class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = "__all__"


class GuideSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guider
        fields = "__all__"


class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = "__all__"

class TransportSerializer(serializers.ModelSerializer):
    train_details = TrainSerializer(many=False, read_only=True)

    class Meta:
        model = Transport
        fields = "__all__"


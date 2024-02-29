from rest_framework import serializers
from .models import Traject,Plan,User,Match,Guider

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        return instance



class TrajectSerializer(serializers.ModelSerializer):
    class Meta:
        model=Traject
        fields=["id","budget","ville","time","person_number","description", "title", "json_content"]

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model=Plan
        fields='__all__'

class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = '__all__'

class GuideSerializer(serializers.ModelSerializer):
    class Meta:
        model=Guider
        fields='__all__'

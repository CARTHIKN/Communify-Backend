from rest_framework import serializers
from verification.models import CustomUser,UserProfile
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re


class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'phone', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_username(self, value):
        """
        Check if the username contains only _ and . symbols without any spaces.
        """
        if re.search(r'[^\w.]+', value):
            raise serializers.ValidationError("Username should contain only letters, digits, underscore, and dot.")
        return value

    def validate_email(self, value):
        """
        Check if the email is already taken.
        """
        if CustomUser.objects.filter(email=value, is_verified=True).exists():
            raise serializers.ValidationError("Email is already taken.")
        return value

    def validate_password(self, value):
        """
        Check if the password length is at least 8 characters.
        """
        if len(value) < 8:
            raise serializers.ValidationError("Password character should be greater than or equal to 8.")
        return value

    def validate_phone(self, value):
        """
        Check if the phone number is exactly 10 characters long.
        """
        if len(value) != 10:
            raise serializers.ValidationError("Please enter the correct phone number.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
            instance.save()
            return instance
        else:
            raise serializers.ValidationError({'password': "Password is not valid."})
        





class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['user', 'bio', 'profile_picture', 'dob', 'remove']
        extra_kwargs = {
            'profile_picture': {'allow_blank': True}  # Allow blank URLs
        }


#------------------------------------------------ADMIN------------------------------------------------



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'phone', 'created_at', 'is_blocked' )

    
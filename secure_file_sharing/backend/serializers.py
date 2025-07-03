from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UploadedFile
import os

User = get_user_model()

class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate_role(self, value):
        # ✅ Allow both client and ops users to sign up
        if value != 'client':
            raise serializers.ValidationError("Only client users can sign up.")
        return value

    def validate_password(self, value):
        # ✅ Validate password strength
        validate_password(value)
        return value

    def create(self, validated_data):
        # ✅ Securely create user using create_user()
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data['role'],
            is_active=False  # Keep inactive until email verification
        )
        return user


class FileUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['file', 'uploaded_by']
        extra_kwargs = {
            'uploaded_by': {'read_only': True}
        }

    def validate_file(self, value):
        # ✅ Cleaner file extension check
        allowed_extensions = ['.pptx', '.docx', '.xlsx']
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError("Only .pptx, .docx, and .xlsx files are allowed.")
        return value
class UploadedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadedFile
        fields = ['id', 'file', 'uploaded_by']
        read_only_fields = ['id', 'file', 'uploaded_by']

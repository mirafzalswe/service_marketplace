from rest_framework import serializers
from django.contrib.auth import authenticate
from django.db import IntegrityError
from .models import User, WorkerProfile

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'role', 'phone', 'avatar', 'is_verified', 'password']
        extra_kwargs = {'password': {'write_only': True}}
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def validate_email(self, value):
        if value and User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def create(self, validated_data):
        try:
            password = validated_data.pop('password')
            user = User.objects.create_user(**validated_data)
            user.set_password(password)
            user.save()
            
            # Create worker profile if role is worker
            if user.role == 'worker':
                WorkerProfile.objects.create(user=user)
            
            return user
        except IntegrityError as e:
            if 'username' in str(e):
                raise serializers.ValidationError({"username": "A user with this username already exists."})
            elif 'email' in str(e):
                raise serializers.ValidationError({"email": "A user with this email already exists."})
            else:
                raise serializers.ValidationError("A user with this information already exists.")

class WorkerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = WorkerProfile
        fields = '__all__'

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Both username and password are required')
        
        return attrs
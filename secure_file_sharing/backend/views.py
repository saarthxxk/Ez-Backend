from django.shortcuts import render
from urllib.parse import quote
from django.core.mail import EmailMessage 
from django.conf import settings
from django.urls import reverse
from .utils import generate_email_token
from .serializers import SignupSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import User
from urllib.parse import unquote
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny

from .utils import verify_email_token
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from .serializers import FileUploadSerializer
from .models import UploadedFile
from rest_framework.parsers import MultiPartParser, FormParser

#for document view
from .models import UploadedFile
from .serializers import UploadedFileSerializer
#for downloading the documents
from django.core.signing import TimestampSigner
from django.urls import reverse
#for serve file from secure lin
from django.core.signing import BadSignature
from django.http import FileResponse
from django.shortcuts import get_object_or_404

permission_classes = [AllowAny]


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token = quote(generate_email_token(user.username), safe='')  
            verification_link = f"http://localhost:8000/verify-email/{token}/"

            # ✨ Send HTML email
            email = EmailMessage(
                subject="Verify Your Email",
                body=f"""
                    <p>Welcome, {user.username}!</p>
                    <p>Please click the link below to verify your email:</p>
                    <p><a href="{verification_link}">Verify Email</a></p>
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            email.content_subtype = "html"
            email.send()

            return Response({"message": "Signup successful. Please check your email to verify."}, status=201)

        return Response(serializer.errors, status=400)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        print("Received token:", token)
        decoded_token = unquote(token)
        username = verify_email_token(decoded_token)
        if not username:
            return Response({"error": "Invalid or expired token."}, status=400)

        user = get_object_or_404(User, username=username)
        user.is_active = True
        user.is_verified = True
        user.save()
        return Response({"message": "Email verified successfully. You can now log in."})


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)

        if not user:
            return Response({"error": "Invalid credentials"}, status=400)

        if not user.is_active:
            return Response({"error": "User is not active"}, status=403)

        if user.role == 'client' and not user.is_verified:
            return Response({"error": "Email not verified"}, status=403)

        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "role": user.role})


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        print("Request data:", request.data)
        print("Request files:", request.FILES)

        if request.user.role != 'ops':
            return Response({"error": "Only Ops users can upload files."}, status=403)

        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(uploaded_by=request.user)
            return Response({"message": "File uploaded successfully."}, status=201)

        return Response(serializer.errors, status=400)

class FileListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'client':
            return Response({"error": "Only clients can view files."}, status=403)

        files = UploadedFile.objects.all()
        serializer = UploadedFileSerializer(files, many=True)
        return Response(serializer.data, status=200)
    
signer = TimestampSigner()
    
class GenerateDownloadLinkView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        if request.user.role != 'client':
            return Response({"error": "Only clients can request download links."}, status=403)

        try:
            file = UploadedFile.objects.get(id=file_id)
        except UploadedFile.DoesNotExist:
            return Response({"error": "File not found"}, status=404)

        # Sign the file ID + username
        raw_token = signer.sign(f"{file_id}:{request.user.username}")
        token = quote(raw_token, safe='')
        download_url = request.build_absolute_uri(
            reverse('secure-download', args=[token])
        )
        return Response({
            "download_link": download_url,
            "message": "success"
        })    

class SecureDownloadView(APIView):
    permission_classes = [AllowAny] 

    def get(self, request, token):
        try:
            decoded_token = unquote(token)
            data = signer.unsign(decoded_token)
            file_id, username = data.split(":")
        except BadSignature:
            return Response({"error": "Invalid or expired link"}, status=400)

        # ✅ Validate that this is a real, active, verified client user
        user = User.objects.filter(username=username, role='client', is_active=True, is_verified=True).first()
        if not user:
            return Response({"error": "Access denied"}, status=403)

        file = get_object_or_404(UploadedFile, id=file_id)
        return FileResponse(file.file, as_attachment=True)

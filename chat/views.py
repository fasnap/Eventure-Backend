from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Message
from . serializers import MessageSerializer, ChatGroupSerializer
from rest_framework.decorators import api_view
from django.core.files.storage import default_storage
from django.http import JsonResponse
import boto3
from django.conf import settings
class ChatGroupView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        groups=request.user.chat_groups.all()
        serializer=ChatGroupSerializer(groups, many=True)
        return Response(serializer.data)

class MessageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id):
        messages = Message.objects.filter(group_id=group_id).order_by('timestamp')
        serializer = MessageSerializer(messages, many=True)
        
        return Response(serializer.data)
import logging

logger = logging.getLogger(__name__)

# @api_view(['POST'])
# def upload_file(request):
#     file = request.FILES['file']
#     logger.info(f"File received: {file.name}")

#     file_name = f"chat_files/{file.name}"
#     file_url = default_storage.save(file_name, file)
#     logger.info(f"File saved at: {file_url}")
#     print("Uploaded file----------", file_url)
#     return JsonResponse({'fileUrl': file_url})

@api_view(['POST'])
def upload_file(request):
    try:
        file = request.FILES['file']
        logger.info(f"File received: {file.name}")

        # Save the file to default storage
        file_name = f"chat_files/{file.name}"
        file_path = default_storage.save(file_name, file)

        # Generate the correct file URL
        file_url = f"https://neweventurebucket.s3.us-east-1.amazonaws.com/{file_path}"
        logger.info(f"File uploaded successfully: {file_url}")
        print("File URL: {file_url}")
        return JsonResponse({'fileUrl': file_url}, status=200)

    except KeyError:
        logger.error("No file found in the request.")
        return JsonResponse({'error': 'No file provided'}, status=400)

    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return JsonResponse({'error': 'File upload failed'}, status=500)



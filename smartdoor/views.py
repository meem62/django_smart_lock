from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
import time
from .models import Device, HardwareData  # Import the Device and HardwareData models
from django.urls import reverse
from .models import User  # Import your User model

import base64
from io import BytesIO
from PIL import Image

from django.core.files.base import ContentFile

import logging


from .models import SpecialGuest
from .serializers import SpecialGuestSerializer

from .models import ViewRequest
from django.utils import timezone

from django.shortcuts import get_object_or_404

from .models import Emergency

from django.views import View
from .models import Owner

import datetime
from django.http import JsonResponse, HttpResponseNotAllowed
import os

from .models import SuccessfulUnsuccessfulEntry

#FOR TESTING RN
from .models import CameraData

from django.http import HttpResponse

from .models import OneTimeGuestEntry

from .models import LocationEntry

from .models import DefaultPinCode


# Temporary storage for reset tokens (should be replaced with a database or cache in production)
password_reset_tokens = {}

# Home page view
def home(request):
    return render(request, 'smartdoor/home.html')  # Ensure template path is correct

# Signup API
@api_view(['POST'])
def signup(request):
    if request.data.get('update_password'):
        email = request.data.get('email')
        new_password = request.data.get('password')

        if not email or not new_password:
            return Response({'error': 'Email and new password are required for password reset'}, 
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            user.set_password(new_password)  
            user.save()
            return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    elif request.data.get('delete_account'):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Email and password are required for account deletion'},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=email)
            if not user.check_password(password):
                return Response({'error': 'Incorrect password'}, status=status.HTTP_400_BAD_REQUEST)
            user.delete()
            return Response({'message': 'Account deleted successfully'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    else:
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')
        password = request.data.get('password')

        if not first_name or not last_name or not email or not password:
            return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=email, first_name=first_name, last_name=last_name, email=email, password=password)

        send_mail(
            'Welcome to Smart Door!',
            'Thank you for signing up. Your account has been successfully created.',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        return Response({'message': 'User registered successfully, please verify your email with OTP.'}, status=status.HTTP_201_CREATED)

# Save WiFi credentials for the device
@api_view(['POST'])
def save_wifi_credentials(request):
    try:
        # Get data from the request
        email = request.data.get('email')
        wifi_ssid = request.data.get('ssid')
        wifi_password = request.data.get('password')
        ip_address = request.data.get('ip_address')

        if not email or not wifi_ssid or not wifi_password or not ip_address:
            return Response({'error': 'Email, WiFi credentials, and IP address are required'}, 
                            status=status.HTTP_400_BAD_REQUEST)

        # Fetch the user by email
        user = User.objects.get(email=email)
        
        # Create or get the device associated with the user
        device = Device.objects.create(user=user, device_id=f"{user.email}_device", paired_at=time.time())

        # Save WiFi credentials and IP address in the device's related model (you can create a separate model for this)
        hardware_data = HardwareData(device=device, data=json.dumps({
            'wifi_ssid': wifi_ssid,
            'wifi_password': wifi_password,
            'ip_address': ip_address
        }))
        hardware_data.save()

        return Response({'message': 'Device WiFi credentials saved successfully'}, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Login API
@api_view(['POST'])
def login(request):
    email = request.data.get('username')  
    password = request.data.get('password')

    failed_attempts = request.session.get('failed_attempts', 0)
    user = authenticate(username=email, password=password)

    if user is not None:
        request.session['failed_attempts'] = 0
        refresh = RefreshToken.for_user(user)
        return Response({'refresh': str(refresh), 'access': str(refresh.access_token)})

    failed_attempts += 1
    request.session['failed_attempts'] = failed_attempts

    if failed_attempts >= 3:
        return Response({'error': 'Invalid credentials', 'reset_password': True}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

@csrf_exempt
def check_email(request):
    if request.method == 'POST':  # Only handle POST requests
        try:
            data = json.loads(request.body)
            email = data.get('email')

            if email is None:
                return JsonResponse({'error': 'No email provided'}, status=status.HTTP_400_BAD_REQUEST)

            if User.objects.filter(email=email).exists():
                return JsonResponse({'message': 'An account with this email already exists.'}, status=status.HTTP_400_BAD_REQUEST)

            return JsonResponse({'message': 'Email is available.'}, status=status.HTTP_200_OK)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    else:
        return JsonResponse({'error': 'Method not allowed. Use POST instead.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


# Save user data after OTP verification
@api_view(['POST'])
def save_user_data(request):
    try:
        data = request.data.get('user_data') or request.data

        if not data:
            return Response({'error': 'No user data received'}, status=status.HTTP_400_BAD_REQUEST)
        
        email = data.get('email')
        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        user = User.objects.get(email=email)
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.save()

        return Response({'message': 'User data saved successfully'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ✅ NEW FUNCTION: Receive phone number from ESP32 and send to Flutter App
@api_view(['POST'])
def receive_phone(request):
    try:
        data = request.data
        phone_number = data.get('phone_number')

        if not phone_number:
            return Response({'error': 'No phone number received'}, status=status.HTTP_400_BAD_REQUEST)

        print(f"Received phone number: {phone_number}")

        # Here you would store the phone number in your database or notify the Flutter app
        return Response({'message': 'Phone number received successfully'}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Request password reset (Step 1: Send reset token via email)
@api_view(['POST'])
def request_password_reset(request):
    email = request.data.get('email')

    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)

    reset_token = get_random_string(length=6)  
    password_reset_tokens[email] = {"token": reset_token, "timestamp": time.time()}  

    send_mail(
        'Password Reset Request',
        f'Your OTP for password reset is: {reset_token}. This code expires in 10 minutes.',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )

    return Response({'message': 'Password reset token sent to email'}, status=status.HTTP_200_OK)

# Confirm password reset (Step 2: Verify token and update password)
@api_view(['POST'])
def confirm_password_reset(request):
    email = request.data.get('email')
    reset_token = request.data.get('reset_token')
    new_password = request.data.get('new_password')

    if not email or not reset_token or not new_password:
        return Response({'error': 'Email, reset token, and new password are required'}, status=status.HTTP_400_BAD_REQUEST)

    if email not in password_reset_tokens or password_reset_tokens[email]["token"] != reset_token:
        return Response({'error': 'Invalid or expired reset token'}, status=status.HTTP_400_BAD_REQUEST)

    if time.time() - password_reset_tokens[email]["timestamp"] > 600:  
        del password_reset_tokens[email]
        return Response({'error': 'Reset token has expired'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()

        del password_reset_tokens[email]  

        return Response({'message': 'Password has been reset successfully'}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
def check_email_ESP32(request, email):
    if request.method == 'GET':  # Use GET instead of POST since you're passing the email in the URL
        try:
            # Check if the email exists in the database
            user = User.objects.filter(email=email).first()

            if user:
                # If the user exists, return a message that the email already exists
                return JsonResponse(
                    {'message': 'An account with this email already exists.'},
                    status=200
                )
            else:
                # If the email doesn't exist, return a message stating it's available
                return JsonResponse({'message': 'Email does not exist. Please try again with a valid email.'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)



# Temporary in-memory storage for email (you can use a database if needed)
stored_email = None

@csrf_exempt
def pass_email(request):
    global stored_email

    if request.method == 'POST':
        try:
            # Parse the incoming data
            data = json.loads(request.body)
            email = data.get('email')

            if email:
                # Store the email temporarily
                stored_email = email
                return JsonResponse({'message': 'Email stored successfully'}, status=200)
            else:
                return JsonResponse({'error': 'No email provided'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    elif request.method == 'GET':
        if stored_email:
            # Return the stored email and delete it from memory
            email = stored_email
            stored_email = None  # Clear the stored email after sending it
            return JsonResponse({'email': email}, status=200)
        else:
            return JsonResponse({'error': 'No email available'}, status=404)

    else:
        return JsonResponse({'error': 'Only POST and GET methods allowed'}, status=405)




# Set up logging for debugging
logger = logging.getLogger(__name__)

@csrf_exempt
def one_time_guest(request, email):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone_number')
            image = data.get('image')  # Expect IP string instead of base64

            if not phone_number or not image:
                return JsonResponse({'error': 'Phone number and image IP are required.'}, status=400)

            entry = OneTimeGuestEntry.objects.create(
                phone_number=phone_number,
                image=image
            )

            return JsonResponse({
                'message': 'Entry created successfully.',
                'id': entry.id,
                'phone_number': entry.phone_number,
                'image': entry.image,
                'date': entry.date,
                'time': entry.time
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format.'}, status=400)

    elif request.method == 'GET':
        entries = OneTimeGuestEntry.objects.all().values(
            'id', 'phone_number', 'image', 'date', 'time'
        )
        return JsonResponse(list(entries), safe=False, status=200)

    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            entry_id = data.get('id')
            if not entry_id:
                return JsonResponse({'error': 'Missing entry ID for deletion.'}, status=400)

            entry = OneTimeGuestEntry.objects.get(id=entry_id)
            entry.delete()
            return JsonResponse({'message': f'Entry {entry_id} deleted successfully.'}, status=200)

        except OneTimeGuestEntry.DoesNotExist:
            return JsonResponse({'error': 'Entry not found.'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format.'}, status=400)

    return JsonResponse({'error': 'Method not allowed.'}, status=405)



@csrf_exempt
def special_guest(request, email, image_id):
    # Only handle special guests for the specific email
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            pin_code = data.get('pin_code')
            name = data.get('name')
            phone_number = data.get('phone_number')
            additional_details = data.get('additional_details')

            # Save or update data for the special guest with the given image_id
            special_guest, created = SpecialGuest.objects.update_or_create(
                image_id=image_id,
                defaults={
                    'pin_code': pin_code,
                    'name': name,
                    'phone_number': phone_number,
                    'additional_details': additional_details,
                }
            )

            return JsonResponse({'message': 'Data saved successfully'}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)

    elif request.method == 'GET':
        try:
            guest = SpecialGuest.objects.get(image_id=image_id)
            return JsonResponse({
                'image_id': guest.image_id,
                'pin_code': guest.pin_code,
                'name': guest.name,
                'phone_number': guest.phone_number,
                'additional_details': guest.additional_details,
            }, status=200)
        except SpecialGuest.DoesNotExist:
            return JsonResponse({'error': 'Special guest not found'}, status=404)

    elif request.method == 'DELETE':
        try:
            # Attempt to delete the guest data using image_id
            guest = SpecialGuest.objects.get(image_id=image_id)
            guest.delete()
            return JsonResponse({'message': 'Data deleted successfully'}, status=200)
        except SpecialGuest.DoesNotExist:
            return JsonResponse({'error': 'Special guest not found'}, status=404)

    else:
        return JsonResponse({'error': 'Invalid method'}, status=405)



@csrf_exempt
def View_Request(request, email):
    if request.method == 'GET':
        notifications = ViewRequest.objects.all()
        notifications_data = list(notifications.values(
            'id', 'name', 'message', 'phone_number', 'savedPinCode', 'CAMImageID', 'timestamp'
        ))
        return JsonResponse(notifications_data, safe=False, status=200)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            message = data.get('message')
            phone_number = data.get('phone_number')
            savedPinCode = data.get('savedPinCode')
            cam_image_id = data.get('CAMImageID')  # 🔹 Capture the field

            new_notification = ViewRequest(
                name=name, 
                message=message, 
                phone_number=phone_number, 
                savedPinCode=savedPinCode,
                CAMImageID=cam_image_id  # 🔹 Save it
            )
            new_notification.save()

            return JsonResponse({'message': 'Notification created successfully!'}, status=201)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)

    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            notification_id = data.get('id')
            notification = ViewRequest.objects.get(id=notification_id)
            notification.delete()

            return JsonResponse({'message': 'Notification deleted successfully!'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
def EmergencyView(request, email):
    if request.method == 'GET':
        emergencies = Emergency.objects.all()
        data = list(emergencies.values('id', 'savedPinCode', 'date', 'time'))
        return JsonResponse(data, safe=False, status=200)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            pin = data.get('savedPinCode')
            date = data.get('date')
            time = data.get('time')

            emergency = Emergency(savedPinCode=pin, date=date, time=time)
            emergency.save()

            return JsonResponse({'message': 'Emergency PIN saved!'}, status=201)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            pin_id = data.get('id')
            entry = Emergency.objects.get(id=pin_id)
            entry.delete()
            return JsonResponse({'message': 'Deleted successfully'}, status=200)
        except Emergency.DoesNotExist:
            return JsonResponse({'error': 'PIN not found'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return JsonResponse({'error': 'Invalid method'}, status=405)



@csrf_exempt
def owner_handler(request, email):
    if request.method == 'GET':
        owners = Owner.objects.all()
        data = list(owners.values())
        return JsonResponse(data, safe=False)

    elif request.method == 'POST':
        try:
            print("📥 Incoming POST body:", request.body)  # Debug line (optional)
            body = json.loads(request.body)
            name = body.get('name')
            phone = body.get('phone_number')
            fingerprint_id = body.get('fingerprint_id')  # could be None

            owner = Owner.objects.filter(name=name, phone_number=phone, scanned=False).first()

            if owner:
                owner.fingerprint_id = fingerprint_id
                owner.scanned = True
                owner.save()
                return JsonResponse({'message': 'Owner updated with fingerprint.'}, status=200)
            else:
                new_owner = Owner(
                    name=name,
                    phone_number=phone,
                    fingerprint_id=fingerprint_id,
                    scanned=True if fingerprint_id is not None else False
                )
                new_owner.save()
                return JsonResponse({'message': 'New owner created and saved.'}, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    elif request.method == 'DELETE':
        try:
            body = json.loads(request.body)
            owner_id = body.get('id')
            entry = Owner.objects.get(id=owner_id)
            entry.delete()
            return JsonResponse({'message': 'Deleted successfully'})
        except Owner.DoesNotExist:
            return JsonResponse({'error': 'Owner not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid method'}, status=405)



@csrf_exempt
def upload_photo(request, email):
    media_dir = "media"

    if request.method == 'POST':
        # Save incoming image
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"photo_{timestamp}.jpg"
        image_data = request.body
        filepath = os.path.join(media_dir, filename)

        with open(filepath, "wb") as f:
            f.write(image_data)

        return JsonResponse({
            "message": "Image received",
            "filename": filename
        })

    elif request.method == 'GET':
        filename = request.GET.get("filename")
        
        if filename:
            filepath = os.path.join(media_dir, filename)
            if os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    return HttpResponse(f.read(), content_type="image/jpeg")
            else:
                return JsonResponse({"error": f"{filename} not found."}, status=404)
        else:
            # No filename given → return list of all files
            files = [f for f in os.listdir(media_dir) if os.path.isfile(os.path.join(media_dir, f))]
            return JsonResponse({
                "message": "List of available images",
                "files": files
            })

    elif request.method == 'DELETE':
        filename = request.GET.get("filename")
        if not filename:
            return JsonResponse({"error": "Filename is required for deletion."}, status=400)

        filepath = os.path.join(media_dir, filename)

        if os.path.exists(filepath):
            os.remove(filepath)
            return JsonResponse({"message": f"{filename} deleted successfully."})
        else:
            return JsonResponse({"error": f"{filename} not found."}, status=404)

    else:
        return HttpResponseNotAllowed(["POST", "GET", "DELETE"])





@csrf_exempt
def successful_unsuccessful_entry(request, email):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            phone_number = data.get('phone_number')
            case = data.get('case')
            camera_image_id = data.get('camera_image_id')
            message = data.get('message')  # 🆕

            entry = SuccessfulUnsuccessfulEntry.objects.create(
                name=name,
                phone_number=phone_number,
                case=case,
                camera_image_id=camera_image_id,
                message=message  # 🆕
            )

            return JsonResponse({'message': 'Entry created successfully!'}, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    elif request.method == 'GET':
        entries = SuccessfulUnsuccessfulEntry.objects.all().values(
            'id', 'name', 'phone_number', 'case', 'camera_image_id', 'message', 'date', 'time'  # 🆕
        )
        return JsonResponse(list(entries), safe=False, status=200)

    elif request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            entry_id = data.get('id')

            if not entry_id:
                return JsonResponse({'error': 'Missing entry ID for deletion.'}, status=400)

            entry = SuccessfulUnsuccessfulEntry.objects.get(id=entry_id)
            entry.delete()

            return JsonResponse({'message': f'Entry {entry_id} deleted successfully.'}, status=200)

        except SuccessfulUnsuccessfulEntry.DoesNotExist:
            return JsonResponse({'error': 'Entry not found.'}, status=404)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format.'}, status=400)

    return JsonResponse({'error': 'Method not allowed'}, status=405)




@csrf_exempt
def location_entry(request, email):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            google_maps_link = data.get('google_maps_link')
            written_location = data.get('written_location')

            if not google_maps_link or not written_location:
                return JsonResponse({'error': 'Missing required fields.'}, status=400)

            entry = LocationEntry.objects.create(
                email=email,
                google_maps_link=google_maps_link,
                written_location=written_location
            )

            return JsonResponse({'message': 'Location saved successfully.'}, status=201)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    elif request.method == 'GET':
        entries = LocationEntry.objects.filter(email=email).order_by('-timestamp')
        data = [{
            'google_maps_link': entry.google_maps_link,
            'written_location': entry.written_location,
            'timestamp': entry.timestamp.isoformat()
        } for entry in entries]
        return JsonResponse(data, safe=False)

    return JsonResponse({'error': 'Invalid method'}, status=405)





@csrf_exempt
def default_pin_code_handler(request, email):
    if request.method == 'GET':
        try:
            entry = DefaultPinCode.objects.filter(email=email).first()
            if entry:
                return JsonResponse({
                    "email": entry.email,
                    "pin_code": entry.pin_code
                }, status=200)
            else:
                return JsonResponse({"message": "No default PIN found."}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            pin = data.get("pin_code")

            if not pin or len(pin) != 6 or not pin.isdigit():
                return JsonResponse({"error": "PIN must be an 6-digit number."}, status=400)

            entry, created = DefaultPinCode.objects.update_or_create(
                email=email,
                defaults={"pin_code": pin}
            )
            return JsonResponse({"message": "Default PIN code saved."}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    elif request.method == 'DELETE':
        try:
            entry = DefaultPinCode.objects.get(email=email)
            entry.delete()
            return JsonResponse({"message": "Deleted successfully."}, status=200)
        except DefaultPinCode.DoesNotExist:
            return JsonResponse({"error": "Entry not found."}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid method."}, status=405)


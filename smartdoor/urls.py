from django.urls import path
from . import views  
from .views import upload_photo
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),  # Ensure home page view exists
    path('signup/', views.signup, name='signup'),  # Signup API
    path('login/', views.login, name='login'),  # Login API with JWT
    path('save-user-data/', views.save_user_data, name='save_user_data'),  # Save user data after OTP verification
    path('check-email/', views.check_email, name='check_email'),  # Check email availability API

    # ✅ Password Reset Paths
    path('request-password-reset/', views.request_password_reset, name='request_password_reset'),  # Request password reset
    path('confirm-password-reset/', views.confirm_password_reset, name='confirm_password_reset'),  # Confirm password reset

    # ✅ Alias for `/reset-password/` to avoid Flutter request issues
    path('reset-password/', views.confirm_password_reset, name='reset_password'),  # Alias to avoid Flutter app error

    # New API to receive phone numbers from ESP32
    path('receive-phone/', views.receive_phone, name='receive_phone'),

    # New endpoint to save Wi-Fi credentials for ESP32
    path('save-wifi-credentials/', views.save_wifi_credentials, name='save_wifi_credentials'),  # Save Wi-Fi credentials

    # New path for ESP32 after emailcheck
     path('check_email_ESP32/<str:email>/', views.check_email_ESP32, name='check_email_ESP32'),

    # Email pass from app to ESP32
    path('pass-email/', views.pass_email, name='pass_email'),



    # URL pattern for handling one-time guest
    path('<str:email>/one_time_guest/', views.one_time_guest, name='one_time_guest'),

    
    # URL pattern for generating PIN
    #path('generate_pin/', views.generate_pin, name='generate_pin'),


    path('<str:email>/special_guest/<str:image_id>/', views.special_guest, name='special_guest'),


    path('<str:email>/View_Request/', views.View_Request, name='ViewRequest'),

    path('<str:email>/Emergency/', views.EmergencyView, name='EmergencyView'),

    path('<str:email>/owner/', views.owner_handler, name='owner_handler'),



    path("<str:email>/upload/", views.upload_photo, name="upload_photo"),


    path('<str:email>/Successful_Unsuccessful_Entry/', views.successful_unsuccessful_entry, name='successful_unsuccessful_entry'),


    path('<str:email>/location/', views.location_entry, name='location_entry'),

    path("<str:email>/default_pin/", views.default_pin_code_handler, name="default_pin_code_handler"),





]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


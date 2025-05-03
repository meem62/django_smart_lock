from django.db import models
from django.contrib.auth.models import User

from datetime import timedelta
from django.utils import timezone



class Device(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=100, unique=True)
    paired_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.device_id}"

class HardwareData(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    data = models.TextField()  # Change to JSONField if you need structured data.
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.device.device_id} data at {self.created_at}"

# Add the new model to store Wi-Fi credentials
class WiFiCredentials(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Link to user
    ssid = models.CharField(max_length=255)  # Wi-Fi SSID
    password = models.CharField(max_length=255)  # Wi-Fi Password

    def __str__(self):
        return f"Wi-Fi credentials for {self.user.email}"


class SpecialGuest(models.Model):
    image_id = models.CharField(max_length=255, unique=True)
    pin_code = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    additional_details = models.TextField()

    def __str__(self):
        return f"SpecialGuest {self.image_id}"





class ViewRequest(models.Model):
    name = models.CharField(max_length=100)
    message = models.TextField()
    savedPinCode = models.CharField(max_length=100, default="")
    phone_number = models.CharField(max_length=20, default="")
    CAMImageID = models.CharField(max_length=255, null=True, blank=True)  # 🔹 Add this field
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.phone_number} - {self.savedPinCode} - {self.timestamp}"



class Emergency(models.Model):
    savedPinCode = models.CharField(max_length=10, null=True)
    date = models.CharField(max_length=20, null=True)
    time = models.CharField(max_length=20, null=True)


    def __str__(self):
        return f"{self.savedPinCode} - {self.timestamp}"




class Owner(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    fingerprint_id = models.IntegerField(null=True, blank=True)
    scanned = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.phone_number} - Scanned: {self.scanned}"





class CameraData(models.Model):
    camera_details = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    image_url = models.URLField()

    def __str__(self):
        return f"{self.camera_details} - {self.phone_number}"



class SuccessfulUnsuccessfulEntry(models.Model):
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    case = models.CharField(max_length=50)
    camera_image_id = models.CharField(max_length=100)
    message = models.CharField(max_length=200, default="")  # 🆕 New field
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.case}"



class OneTimeGuestEntry(models.Model):
    phone_number = models.CharField(max_length=20)
    image = models.ImageField(upload_to='one_time_guests/')
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.phone_number} - {self.date} {self.time}"



class LocationEntry(models.Model):
    email = models.EmailField()
    google_maps_link = models.TextField()
    written_location = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} - {self.written_location}"




class DefaultPinCode(models.Model):
    email = models.EmailField()
    pin_code = models.CharField(max_length=6)  # 6-digit numeric string

    def __str__(self):
        return f"{self.email} - {self.pin_code}"



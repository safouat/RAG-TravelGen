from django.db import models
import json
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class User(AbstractUser):
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255)
    username = None

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    

class Traject(models.Model):
    userId=models.IntegerField(default=1)
    datetime = models.DateTimeField(default=timezone.now)
    budget = models.CharField(max_length=100)  # Adjust max_length as needed
    ville = models.CharField(max_length=100)  # Adjust max_length as needed
    time = models.CharField(max_length=100)
    person_number = models.IntegerField()
    json_content = models.JSONField()
    description = models.CharField(max_length=2000,default='none')
    title = models.CharField(max_length=255,default='none')

    def save(self, *args, **kwargs):
        # Serialize the JSON content before saving
        self.json_content = json.dumps(self.json_content)
        super().save(*args, **kwargs)

class Plan(models.Model):
        userId=models.IntegerField(default=1)
        traject_id=models.ForeignKey(Traject, on_delete=models.CASCADE, default=1, null=True, blank=True)
        json_content = models.JSONField()
        def save(self, *args, **kwargs):
        # Serialize the JSON content before saving
            self.json_content = json.dumps(self.json_content)
            super().save(*args, **kwargs)

class Match(models.Model):
     date=models.DateField()
     country1=models.CharField(max_length=100)
     flag1=models.CharField(max_length=100,default='none')
     country2=models.CharField(max_length=100)
     flag2=models.CharField(max_length=100,default='none')
     stadium=models.CharField(max_length=100,default='none')
     city=models.CharField(max_length=100,default='none')
     title=models.CharField(max_length=100,default='none')

class Guider(models.Model):
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255, unique=True)
    ville= models.CharField(max_length=255)
    description= models.CharField(max_length=1000,default='none')
    avatar=models.CharField(max_length=255,default='none')


class Transport(models.Model):
    city = models.CharField(max_length=255)
    description = models.CharField(max_length=255, unique=True)
    picture= models.CharField(max_length=255)
    transportType= models.CharField(max_length=1000)
     
     





        



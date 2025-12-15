from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    
    ROLE_CHOICES = [
        ('team_member', 'Team Member'),
        ('rota_manager', 'Rota Manager'),
        ('service_manager', 'Service Manager'),
        ('system_admin', 'System Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='team_member')

    TEAM_CHOICES = [
        ('Alpha', 'Team Alpha'),
        ('Bravo', 'Team Bravo'),
        ('Charlie', 'Team Charlie'),
        ('Delta', 'Team Delta'),
    ]
    team = models.CharField(max_length=20, choices=TEAM_CHOICES, blank=True, null=True)

    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    default_start_time = models.TimeField(null=True, blank=True, help_text="e.g. 09:00")
    default_end_time = models.TimeField(null=True, blank=True, help_text="e.g. 17:00")
    timezone = models.CharField(max_length=50, default='Europe/London')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username
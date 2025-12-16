from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    responsibilities = models.TextField(blank=True)
    access_level = models.CharField(max_length=50, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    timezone = models.CharField(max_length=50, default='Europe/London')
    default_start_time = models.TimeField(null=True, blank=True)
    default_end_time = models.TimeField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Skill(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)

    ROLE_CHOICES = [
        ('team_member', 'Team Member'),
        ('rota_manager', 'Rota Manager'),
        ('service_manager', 'Service Manager'),
        ('system_admin', 'System Admin'),
        ('automation_bot', 'Automation Bot'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='team_member')
    role_profile = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL)

    team = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL, related_name='members')
    skills = models.ManyToManyField(Skill, blank=True)

    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    default_start_time = models.TimeField(null=True, blank=True, help_text="e.g. 09:00")
    default_end_time = models.TimeField(null=True, blank=True, help_text="e.g. 17:00")
    timezone = models.CharField(max_length=50, default='Europe/London')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.username

    def has_role(self, *codes: str) -> bool:
        if self.role in codes:
            return True
        if self.role_profile and self.role_profile.code in codes:
            return True
        return False

    @property
    def access_level(self):
        if self.role_profile:
            return self.role_profile.access_level
        return None

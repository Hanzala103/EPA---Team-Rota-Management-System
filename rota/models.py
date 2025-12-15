from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from accounts.models import Team, Role

class Shift(models.Model):
    title = models.CharField(max_length=100)
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    start = models.DateTimeField()
    end = models.DateTimeField()
    team = models.ForeignKey(Team, null=True, blank=True, on_delete=models.SET_NULL)
    role_required = models.ForeignKey(Role, null=True, blank=True, on_delete=models.SET_NULL)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_on_call = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    def clean(self):
        if self.start >= self.end:
            raise ValidationError("Shift end time must be after start time.")
        conflicts = AvailabilitySlot.objects.filter(
            user=self.user,
            end__gt=self.start,
            start__lt=self.end,
            slot_type__in=['unavailable', 'leave']
        )
        if conflicts.exists():
            raise ValidationError("Shift overlaps with an unavailable or leave period.")


class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey('accounts.CustomUser', null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_leaves')

    def __str__(self):
        return f"{self.user} - Leave {self.start_date} to {self.end_date} ({self.status})"


class AvailabilitySlot(models.Model):
    SLOT_TYPES = [
        ('available', 'Available'),
        ('unavailable', 'Unavailable'),
        ('on_call', 'On Call'),
        ('leave', 'Leave'),
    ]

    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='availability')
    start = models.DateTimeField()
    end = models.DateTimeField()
    slot_type = models.CharField(max_length=20, choices=SLOT_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start']
        indexes = [
            models.Index(fields=['user', 'start', 'end']),
        ]

    def clean(self):
        if self.start >= self.end:
            raise ValidationError("Availability end time must be after start time.")

        overlap = AvailabilitySlot.objects.filter(
            user=self.user,
            end__gt=self.start,
            start__lt=self.end
        ).exclude(pk=self.pk)
        if overlap.exists():
            raise ValidationError("Availability overlaps with an existing slot.")

    def __str__(self):
        return f"{self.user} {self.slot_type} from {self.start} to {self.end}"


class Assignment(models.Model):
    ASSIGNMENT_TYPES = [
        ('primary', 'Primary'),
        ('backup', 'Backup'),
        ('on_call', 'On Call'),
    ]

    shift = models.ForeignKey(Shift, on_delete=models.CASCADE, related_name='assignments')
    user = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE)
    assignment_type = models.CharField(max_length=20, choices=ASSIGNMENT_TYPES, default='primary')

    class Meta:
        unique_together = ('shift', 'user', 'assignment_type')

    def __str__(self):
        return f"{self.user} as {self.assignment_type} for {self.shift}"


class Holiday(models.Model):
    name = models.CharField(max_length=100)
    date = models.DateField()
    region = models.CharField(max_length=100, default='UK')

    class Meta:
        unique_together = ('date', 'region')
        ordering = ['date']

    def __str__(self):
        return f"{self.name} ({self.region})"


class ChangeLog(models.Model):
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    entity_type = models.CharField(max_length=100)
    entity_id = models.CharField(max_length=100)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(default=timezone.now)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.entity_type} {self.action} by {self.user or 'system'}"
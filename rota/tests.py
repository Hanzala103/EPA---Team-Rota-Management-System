from datetime import date, datetime, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import CustomUser, Team
from rota.models import Shift, LeaveRequest, AvailabilitySlot

class RotaTests(TestCase):
    def setUp(self):
        # Create manager
        self.manager = CustomUser.objects.create_user(
            username='manager', email='m@rota.com', password='test123', role='rota_manager')
        self.manager.is_staff = True
        self.manager.save()

        # Create team member
        self.member = CustomUser.objects.create_user(
            username='john', email='j@rota.com', password='test123', role='team_member')
        self.team = Team.objects.create(name="Team QA")
        self.member.team = self.team
        self.member.save()

    def test_conflict_detection_leave(self):
        # Approve leave
        leave = LeaveRequest.objects.create(
            user=self.member, start_date=date(2025,12,20), end_date=date(2025,12,22), status='approved')
        
        # Try create shift during leave
        self.client.login(username='manager', password='test123')
        response = self.client.post(reverse('create-shift'), {
            'title': 'Conflict', 'user': self.member.id,
            'start': '2025-12-21T09:00',
            'end': '2025-12-21T17:00'
        })
        self.assertContains(response, "approved leave")  # Red error appears

    def test_only_manager_sees_pending(self):
        self.client.login(username='john', password='test123')
        response = self.client.get(reverse('leave_pending'))
        self.assertEqual(response.status_code, 302)  # Redirects for non-manager

    def test_reports_shows_data(self):
        Shift.objects.create(user=self.member, title="Morning", start=datetime(2025,12,5,9,0), end=datetime(2025,12,5,17,0), status='approved')
        self.client.login(username='manager', password='test123')
        response = self.client.get(reverse('reports'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "john")
        self.assertContains(response, "8")  # 8 hours

    def test_availability_conflict_validation(self):
        slot = AvailabilitySlot(
            user=self.member,
            start=datetime(2025, 12, 5, 9, 0),
            end=datetime(2025, 12, 5, 17, 0),
            slot_type='available',
        )
        slot.clean()
        slot.save()

        overlapping = AvailabilitySlot(
            user=self.member,
            start=datetime(2025, 12, 5, 16, 0),
            end=datetime(2025, 12, 5, 18, 0),
            slot_type='unavailable',
        )
        with self.assertRaises(ValidationError):
            overlapping.clean()

    def test_shift_respects_unavailability(self):
        AvailabilitySlot.objects.create(
            user=self.member,
            start=datetime(2025, 12, 10, 9, 0),
            end=datetime(2025, 12, 10, 12, 0),
            slot_type='unavailable',
        )

        shift = Shift(
            user=self.member,
            title="Conflict shift",
            start=datetime(2025, 12, 10, 10, 0),
            end=datetime(2025, 12, 10, 18, 0),
            team=self.team,
        )
        with self.assertRaises(ValidationError):
            shift.clean()
from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("calendar/", views.calendar_view, name="calendar"),
    path("shifts/", views.shifts_view, name="shifts"),
    
    # Fixed: the template uses name="pending-shifts", not "pending"
    path("pending/", views.pending_shifts, name="pending-shifts"),
    
    # This one now matches the function you renamed
    path("create/", views.create_shift, name="create-shift"),
    
    # Optional but good to have (used by approve/reject buttons)
    path("approve/<int:shift_id>/", views.approve_shift, name="approve-shift"),
    path("reject/<int:shift_id>/", views.reject_shift, name="reject-shift"),

    path('leave/request/', views.leave_request_view, name='leave_request'),
    path('leave/pending/', views.leave_pending_view, name='leave_pending'),
    path('leave/approve/<int:pk>/', views.leave_approve, name='leave_approve'),
    path('leave/reject/<int:pk>/', views.leave_reject, name='leave_reject'),

    path('reports/', views.reports_view, name='reports'),
    path('export/csv/', views.export_shifts_csv, name='export_csv'),
]
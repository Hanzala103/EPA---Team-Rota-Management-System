from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from calendar import monthrange
from datetime import date, timedelta
from .models import Shift
from .forms import ShiftForm
from .models import LeaveRequest
from django.utils import timezone
from django.contrib import messages
from django.http import HttpResponse
import csv
from datetime import datetime, timedelta
from accounts.models import CustomUser


# -----------------------------
# ROLE CHECK (safe)
# -----------------------------
def is_manager(user):
    return user.has_role('rota_manager', 'service_manager', 'system_admin') or user.is_staff or user.is_superuser

def is_service_or_above(user):
    return user.has_role('service_manager', 'system_admin') or user.is_staff or user.is_superuser

def has_conflict(user, start, end, shift_id=None):
    from datetime import datetime
    from .models import Shift, LeaveRequest  # <-- THIS LINE WAS MISSING

    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())

    # Check overlapping shifts
    overlapping_shifts = Shift.objects.filter(user=user).exclude(pk=shift_id)
    for shift in overlapping_shifts:
        if start_dt < shift.end and end_dt > shift.start:
            return True, "You already have a shift during this time."

    # Check approved leave
    approved_leaves = LeaveRequest.objects.filter(
        user=user,
        status='approved',
        start_date__lte=end,
        end_date__gte=start
    )
    if approved_leaves.exists():
        return True, "You have approved leave during this period."

    return False, ""

# -----------------------------
# DASHBOARD
# -----------------------------
@login_required
def dashboard_view(request):
    return render(request, "rota/dashboard.html")
    

# -----------------------------
# CALENDAR VIEW
# -----------------------------
@login_required
def calendar_view(request):
    today = date.today()
    year = int(request.GET.get("year", today.year))
    month = int(request.GET.get("month", today.month))

    # Handle month overflow/underflow
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])

    if is_manager(request.user):
        shifts = Shift.objects.filter(start__date__gte=first_day, start__date__lte=last_day)
    else:
        shifts = Shift.objects.filter(user=request.user, start__date__gte=first_day, start__date__lte=last_day)

    month_calendar = []
    start_week = first_day - timedelta(days=first_day.weekday())

    for week in range(6):
        week_days = []
        for day in range(7):
            current = start_week + timedelta(days=week * 7 + day)
            day_shifts = shifts.filter(start__date=current)

            week_days.append({
                "date": current,
                "shifts": day_shifts,
                "is_current_month": current.month == month
            })
        month_calendar.append(week_days)

    context = {
        "calendar": month_calendar,
        "month": month,
        "year": year,
    }

    return render(request, "rota/calendar.html", context)


# -----------------------------
# ALL SHIFTS (staff + manager)
# -----------------------------
@login_required
def shifts_view(request):
    if is_manager(request.user):
        shifts = Shift.objects.all().order_by("start")
    else:
        shifts = Shift.objects.filter(user=request.user).order_by("start")
    return render(request, "rota/shifts.html", {"shifts": shifts})


# -----------------------------
# CREATE NEW SHIFT (manager only)
# -----------------------------
@user_passes_test(is_manager)
@login_required
def create_shift(request):
    if request.method == "POST":
        form = ShiftForm(request.POST)
        if form.is_valid():
            shift = form.save(commit=False)
            conflict_found, conflict_message = has_conflict(
                user=shift.user,
                start=shift.start.date(),
                end=shift.end.date(),
                shift_id=None
            )
            if conflict_found:
                messages.error(request, f"Cannot create shift: {conflict_message}")
            else:
                shift.save()
                messages.success(request, "Shift created successfully!")
                return redirect('shifts')
    else:
        form = ShiftForm()
    return render(request, "rota/shift_create.html", {"form": form})


# -----------------------------
# PENDING SHIFTS (manager only)
# -----------------------------
@user_passes_test(is_manager)
@login_required
def pending_shifts(request):
    shifts = Shift.objects.filter(status="pending")
    return render(request, "rota/pending_shift.html", {"shifts": shifts})  # Changed to singular


# -----------------------------
# APPROVE SHIFT
# -----------------------------
@user_passes_test(is_manager)
@login_required
def approve_shift(request, shift_id):
    shift = get_object_or_404(Shift, id=shift_id)
    shift.status = "approved"
    shift.save()
    return redirect("pending-shifts")


# -----------------------------
# REJECT SHIFT
# -----------------------------
@user_passes_test(is_manager)
@login_required
def reject_shift(request, shift_id):
    shift = get_object_or_404(Shift, id=shift_id)
    shift.status = "rejected"
    shift.save()
    return redirect("pending-shifts")


# -----------------------------
# LEAVE REQUEST VIEW
# -----------------------------
@login_required
def leave_request_view(request):
    if request.method == 'POST':
        start = request.POST['start_date']
        end = request.POST['end_date']
        reason = request.POST.get('reason', '')
        LeaveRequest.objects.create(
            user=request.user,
            start_date=start,
            end_date=end,
            reason=reason
        )
        messages.success(request, "Leave request submitted!")
        return redirect('dashboard')
    return render(request, 'rota/leave_request.html')


# -----------------------------
# PENDING LEAVE VIEW
# -----------------------------
@user_passes_test(is_manager)
@login_required
def leave_pending_view(request):
    leaves = LeaveRequest.objects.filter(status='pending').order_by('requested_at')
    return render(request, 'rota/leave_pending.html', {'leaves': leaves})


# -----------------------------
# LEAVE APPROVE
# -----------------------------
@user_passes_test(is_manager)
@login_required
def leave_approve(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    leave.status = 'approved'
    leave.reviewed_by = request.user
    leave.reviewed_at = timezone.now()
    leave.save()
    messages.success(request, f"Leave approved for {leave.user}")
    return redirect('leave_pending')


# -----------------------------
# LEAVE REJECT
# -----------------------------
@user_passes_test(is_manager)
@login_required
def leave_reject(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)
    leave.status = 'rejected'
    leave.reviewed_by = request.user
    leave.reviewed_at = timezone.now()
    leave.save()
    messages.success(request, f"Leave rejected for {leave.user}")
    return redirect('leave_pending')


# -----------------------------
# PEPORTS VIEW
# -----------------------------
@login_required
@user_passes_test(lambda u: u.role in ['rota_manager', 'system_admin'])
def reports_view(request):
    today = date.today()
    month_start = today.replace(day=1)
    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

    # Hours per user this month
    users = CustomUser.objects.filter(role='team_member')
    user_stats = []
    for user in users:
        hours = Shift.objects.filter(
            user=user,
            start__date__gte=month_start,
            start__date__lte=month_end,
            status='approved'
        ).count() * 8  # assume 8h shift
        user_stats.append({'user': user, 'hours': hours})

    # Coverage gaps
    days = []
    current = month_start
    while current <= month_end:
        count = Shift.objects.filter(start__date=current, status='approved').count()
        days.append({'date': current, 'count': count, 'gap': count < 2})
        current += timedelta(days=1)

    context = {
        'user_stats': user_stats,
        'days': days,
        'month': today.strftime("%B %Y")
    }
    return render(request, 'rota/reports.html', context)


#----------------------------
# EXPORT REPORTS CSV
#----------------------------
@login_required
@user_passes_test(lambda u: u.role in ['rota_manager', 'system_admin'])
def export_shifts_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="shifts_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['User', 'Title', 'Start', 'End', 'Status'])
    
    shifts = Shift.objects.all().order_by('start')
    for shift in shifts:
        writer.writerow([shift.user.username, shift.title, shift.start, shift.end, shift.status])
    
    return response
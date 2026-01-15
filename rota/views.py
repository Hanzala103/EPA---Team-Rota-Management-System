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
# ROLE CHECKS
# -----------------------------
# Editors = can create/approve shifts and manage leave approvals
def is_editor(user):
    return user.has_role('rota_manager', 'system_admin') or user.is_staff or user.is_superuser

# Reporting/read elevated roles = can view team data and reports
def is_reporting(user):
    return user.has_role('service_manager', 'rota_manager', 'system_admin') or user.is_staff or user.is_superuser

def has_conflict(user, start, end, shift_id=None):
    from datetime import datetime
    from .models import Shift, LeaveRequest  # <-- THIS LINE WAS MISSING

    start_dt = datetime.combine(start, datetime.min.time())
    end_dt = datetime.combine(end, datetime.max.time())
    if timezone.is_naive(start_dt):
        start_dt = timezone.make_aware(start_dt)
    if timezone.is_naive(end_dt):
        end_dt = timezone.make_aware(end_dt)

    # Check overlapping shifts
    overlapping_shifts = Shift.objects.filter(user=user).exclude(pk=shift_id)
    for shift in overlapping_shifts:
        if start_dt < shift.end and end_dt > shift.start:
            # Include the user's display name in the message
            display = user.get_full_name() or user.username
            return True, f"{display} already has a shift during this time."

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

    if is_reporting(request.user):
        shifts = Shift.objects.filter(start__date__gte=first_day, start__date__lte=last_day)
    else:
        shifts = Shift.objects.filter(user=request.user, start__date__gte=first_day, start__date__lte=last_day)

    # Also include leave requests that overlap this month (approved or pending)
    if is_reporting(request.user):
        leaves = LeaveRequest.objects.filter(end_date__gte=first_day, start_date__lte=last_day)
    else:
        leaves = LeaveRequest.objects.filter(user=request.user, end_date__gte=first_day, start_date__lte=last_day)

    month_calendar = []
    start_week = first_day - timedelta(days=first_day.weekday())

    for week in range(6):
        week_days = []
        for day in range(7):
            current = start_week + timedelta(days=week * 7 + day)
            day_shifts = shifts.filter(start__date=current)

            # leaves that include this day
            day_leaves = leaves.filter(start_date__lte=current, end_date__gte=current)

            week_days.append({
                "date": current,
                "shifts": day_shifts,
                "leaves": day_leaves,
                "is_current_month": current.month == month
            })
        month_calendar.append(week_days)

    context = {
        "calendar": month_calendar,
        "month": month,
        "year": year,
    }
    # indicate whether current user can manage/report (used in templates)
    context["is_manager"] = is_reporting(request.user)

    return render(request, "rota/calendar.html", context)


# -----------------------------
# ALL SHIFTS (staff + manager)
# -----------------------------
@login_required
def shifts_view(request):
    # Base queryset depends on role: managers/reporting see all, others see only their shifts
    if is_reporting(request.user):
        shifts_qs = Shift.objects.all().order_by("start")
    else:
        shifts_qs = Shift.objects.filter(user=request.user).order_by("start")

    # Filters from GET params
    title_q = request.GET.get('title', '').strip()
    status_q = request.GET.get('status', 'all')
    user_q = request.GET.get('user', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()

    if title_q:
        # allow partial matches
        shifts_qs = shifts_qs.filter(title__icontains=title_q)

    if status_q and status_q != 'all':
        shifts_qs = shifts_qs.filter(status=status_q)

    # Allow managers to filter by user (partial username)
    users = None
    if user_q and is_reporting(request.user):
        shifts_qs = shifts_qs.filter(user__username__icontains=user_q)
    if is_reporting(request.user):
        users = CustomUser.objects.values_list('username', flat=True).distinct().order_by('username')

    # Date range filtering (on start date)
    from datetime import date as _date
    if date_from:
        try:
            d1 = _date.fromisoformat(date_from)
            shifts_qs = shifts_qs.filter(start__date__gte=d1)
        except ValueError:
            pass
    if date_to:
        try:
            d2 = _date.fromisoformat(date_to)
            shifts_qs = shifts_qs.filter(start__date__lte=d2)
        except ValueError:
            pass

    # Provide list of existing titles for the datalist/autocomplete
    titles = Shift.objects.values_list('title', flat=True).distinct().order_by('title')

    context = {
        "shifts": shifts_qs,
        "titles": titles,
        "users": users,
        "selected_title": title_q,
        "selected_status": status_q,
        "selected_date_from": date_from,
        "selected_date_to": date_to,
        "selected_user": user_q,
        "is_manager": is_reporting(request.user),
    }
    return render(request, "rota/shifts.html", context)


# -----------------------------
# CREATE NEW SHIFT (manager only)
# -----------------------------
@user_passes_test(is_editor)
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
@user_passes_test(is_editor)
@login_required
def pending_shifts(request):
    shifts = Shift.objects.filter(status="pending")
    return render(request, "rota/pending_shift.html", {"shifts": shifts})  # Changed to singular


# -----------------------------
# APPROVE SHIFT
# -----------------------------
@user_passes_test(is_editor)
@login_required
def approve_shift(request, shift_id):
    shift = get_object_or_404(Shift, id=shift_id)
    shift.status = "approved"
    shift.save()
    return redirect("pending-shifts")


# -----------------------------
# REJECT SHIFT
# -----------------------------
@user_passes_test(is_editor)
@login_required
def reject_shift(request, shift_id):
    shift = get_object_or_404(Shift, id=shift_id)
    shift.status = "rejected"
    shift.save()
    return redirect("pending-shifts")


# -----------------------------
# DELETE SHIFT (confirmation + POST)
# -----------------------------
@user_passes_test(is_editor)
@login_required
def delete_shift(request, shift_id):
    shift = get_object_or_404(Shift, id=shift_id)
    if request.method == "POST":
        shift.delete()
        messages.success(request, "Shift deleted.")
        return redirect("shifts")
    return render(request, "rota/shift_delete.html", {"shift": shift})


# -----------------------------
# LEAVE REQUEST VIEW
# -----------------------------
@login_required
def leave_request_view(request):
    # Only team members should submit leave requests
    user_requests = LeaveRequest.objects.filter(user=request.user).order_by('-requested_at')

    if request.method == 'POST':
        if request.user.role != 'team_member':
            messages.error(request, "Only team members can submit leave requests.")
            return redirect('leave_request')

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
        return redirect('leave_request')

    return render(request, 'rota/leave_request.html', {'user_requests': user_requests})


# -----------------------------
# PENDING LEAVE VIEW
# -----------------------------
@user_passes_test(is_editor)
@login_required
def leave_pending_view(request):
    # Show both pending and approved leaves (rename pending view to 'Leaves')
    leaves = LeaveRequest.objects.filter(status__in=['pending', 'approved']).order_by('-requested_at')
    return render(request, 'rota/leaves.html', {'leaves': leaves})


# -----------------------------
# LEAVE APPROVE
# -----------------------------
@user_passes_test(is_editor)
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
@user_passes_test(is_editor)
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
# REPORTS VIEW
# -----------------------------
@login_required
@user_passes_test(is_reporting)
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
@user_passes_test(is_reporting)
def export_shifts_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="shifts_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['User', 'Title', 'Start', 'End', 'Status'])
    
    shifts = Shift.objects.all().order_by('start')
    for shift in shifts:
        writer.writerow([shift.user.username, shift.title, shift.start, shift.end, shift.status])
    
    return response

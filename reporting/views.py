from django.shortcuts import render
from datetime import date, timedelta
from rota.models import Shift


# -----------------------------------
# MAIN REPORTS HOME SCREEN
# -----------------------------------
def reports_home(request):
    total_shifts = Shift.objects.count()
    upcoming_shifts = Shift.objects.filter(start__date__gte=date.today()).count()

    context = {
        "total_shifts": total_shifts,
        "upcoming_shifts": upcoming_shifts,
    }

    return render(request, "reporting/reports_home.html", context)


# -----------------------------------
# DAILY REPORT
# -----------------------------------
def daily_report(request):
    selected_date = request.GET.get("date")

    if selected_date:
        shifts = Shift.objects.filter(start__date=selected_date)
    else:
        shifts = []

    return render(request, "reporting/daily.html", {
        "shifts": shifts,
        "selected_date": selected_date
    })


# -----------------------------------
# WEEKLY REPORT
# -----------------------------------
def weekly_report(request):
    selected_date = request.GET.get("date")

    if selected_date:
        selected_date = date.fromisoformat(selected_date)
        week_start = selected_date - timedelta(days=selected_date.weekday())
        week_end = week_start + timedelta(days=6)

        shifts = Shift.objects.filter(
            start__date__gte=week_start,
            start__date__lte=week_end
        )
    else:
        week_start = week_end = None
        shifts = []

    return render(request, "reporting/weekly.html", {
        "shifts": shifts,
        "week_start": week_start,
        "week_end": week_end
    })


# -----------------------------------
# MONTHLY REPORT
# -----------------------------------
def monthly_report(request):
    selected_month = request.GET.get("month")
    selected_year = request.GET.get("year")

    if selected_month and selected_year:
        shifts = Shift.objects.filter(
            start__year=selected_year,
            start__month=selected_month
        )
    else:
        shifts = []

    return render(request, "reporting/monthly.html", {
        "shifts": shifts,
        "selected_month": selected_month,
        "selected_year": selected_year
    })

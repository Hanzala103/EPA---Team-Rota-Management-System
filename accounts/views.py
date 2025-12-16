from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist

from .forms import RegisterForm, LoginForm
from .models import CustomUser, Team


def login_view(request):
    # If already logged in → go straight to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.user  # From form clean
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.get_full_name() or user.email}!")
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid username/email or password.")
    else:
        form = LoginForm()

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful – welcome!")
            return redirect("dashboard")  # Or 'profile'
        else:
            messages.error(request, "Error – check form.")
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})


@login_required
def profile_view(request):
    if request.method == 'POST':
        user = request.user
        user.phone = request.POST.get('phone', '')
        user.department = request.POST.get('department', '')
        team_id = request.POST.get('team')
        user.team = Team.objects.filter(id=team_id).first() if team_id else None
        user.default_start_time = request.POST.get('default_start_time') or None
        user.default_end_time = request.POST.get('default_end_time') or None
        user.timezone = request.POST.get('timezone', 'Europe/London')
        user.save()
        messages.success(request, "Profile updated successfully!")

    teams = Team.objects.all()
    return render(request, 'accounts/profile.html', {'user': request.user, 'teams': teams})

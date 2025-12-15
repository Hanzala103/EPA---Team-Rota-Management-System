from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_home, name='reports-home'),

    # reports
    path('daily/', views.daily_report, name='daily-report'),
    path('weekly/', views.weekly_report, name='weekly-report'),
    path('monthly/', views.monthly_report, name='monthly-report'),
]

from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect   # ← add this line

# Simple root view that redirects to the dashboard (or login)
def root_view(request):
    return redirect('dashboard')         # after login, user goes to dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('rota/', include('rota.urls')),
    path('reports/', include('reporting.urls')),

    # This line fixes the 404 on the homepage
    path('', root_view, name='root'),
]
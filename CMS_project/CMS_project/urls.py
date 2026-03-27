from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Redirect homepage to dashboard (we'll create it soon)
    path('', lambda request: redirect('dashboard/'), name='home'),
    
    # Include our apps (we'll add more later)
    # path('accounts/', include('accounts.urls')),
    # path('core/', include('core.urls')),
]

# Optional: Add this at the bottom for better error pages during development
# handler404 = 'core.views.custom_404'
# handler500 = 'core.views.custom_500'
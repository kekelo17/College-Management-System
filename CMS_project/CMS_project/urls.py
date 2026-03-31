from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView
from core.views import dashboard, landing_page

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Root landing page
    path('', landing_page, name='landing'),
    
    # Shortcut dashboard URL redirect
    path('dashboard/', RedirectView.as_view(url='/core/dashboard/', permanent=False), name='dashboard_shortcut'),
    
    # App URLs
    path('accounts/', include('accounts.urls')),
    path('core/', include('core.urls')),
    path('students/', include('students.urls')),
    path('teachers/', include('teachers.urls')),
    path('courses/', include('courses.urls')),
    path('attendance/', include('attendance.urls')),
    path('results/', include('results.urls')),
    path('fees/', include('fees.urls')),
    path('timetable/', include('timetable.urls')),
    path('notifications/', include('notifications.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

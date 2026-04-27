"""
Definition of urls for DjangoWebProject1.
"""

from datetime import datetime
from django.urls import path, include
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView
from app import forms, views

from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings


urlpatterns = [
    path('contact/', views.contact, name='contact'),
    path('about/', views.about, name='about'),
    path('delivery/', views.delivery, name='delivery'),
    path('registration/', views.registration, name='registration'),
    path('login/',
         LoginView.as_view(
             template_name='app/login.html',
             authentication_form=forms.BootstrapAuthenticationForm,
             extra_context={
                 'title': 'Авторизация',
                 'year': datetime.now().year,
             }
         ),
         name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('admin/', admin.site.urls),

    # Include app-specific urls
    path('', include('app.urls', namespace='app')),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns()
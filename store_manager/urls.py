from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static

def root_redirect(request):
    """Redirection racine vers login"""
    return redirect('accounts:login')

urlpatterns = [
    path('admin/', admin.site.urls),

    # Redirection racine
    path('', root_redirect, name='root'),

    # URLs de l'app accounts (avec namespace)
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),

    # URLs de l'app core (avec namespace)
    path('core/', include('apps.core.urls', namespace='core')),

    # Redirections directes pour compatibilité
    path('login/', lambda r: redirect('accounts:login'), name='login_redirect'),
    path('dashboard/', lambda r: redirect('core:dashboard'), name='dashboard_redirect'),
    path('caisse/', lambda r: redirect('core:caisse'), name='caisse_redirect'),
]

# En mode DEBUG, servir les fichiers médias
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

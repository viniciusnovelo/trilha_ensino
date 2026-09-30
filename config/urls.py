from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('contas/', include('django.contrib.auth.urls')), # Motor de login
    path('', include('curriculo.urls')),
    path('gamificacao/', include('gamificacao.urls')),
]
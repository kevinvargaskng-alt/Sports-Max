from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='home'),
    path('ayuda/', views.ayuda, name='ayuda'),
    
    # ── Rutas Legales & Cumplimiento ──────────────────────────
    path('privacidad/', views.politica_privacidad, name='politica_privacidad'),
    path('terminos/', views.terminos_condiciones, name='terminos_condiciones'),
    path('cookies/', views.politica_cookies, name='politica_cookies'),

    # ── SEO Técnico ───────────────────────────────────────────
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),
]


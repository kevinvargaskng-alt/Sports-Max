import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from interfichas.models import TorneoInterfichas
from django.test import RequestFactory
from django.contrib.auth import get_user_model
from interfichas.views import reporte_torneo

User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first()
if not admin_user:
    admin_user = User.objects.first()

torneo = TorneoInterfichas.objects.first()
if torneo:
    rf = RequestFactory()
    req = rf.get(f'/interfichas/torneo/{torneo.pk}/reporte/', HTTP_HOST='127.0.0.1')
    req.user = admin_user
    res = reporte_torneo(req, torneo.pk)
    print("STATUS CODE:", res.status_code)
    print("Contiene 'Cronograma Oficial':", "Cronograma Oficial" in res.content.decode('utf-8'))
    print("Contiene 'badge-grupo':", "badge-grupo" in res.content.decode('utf-8'))
    print("Total bytes rendered:", len(res.content))
else:
    print("No hay torneos en la base de datos.")

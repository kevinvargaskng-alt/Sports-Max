import os
import sys
import socket
import subprocess
from django.apps import AppConfig

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

class InicioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inicio'

    def ready(self):
        # Arrancar servidor IA automáticamente al hacer runserver
        if 'runserver' in sys.argv:
            # RUN_MAIN == 'true' asegura que se ejecute solo en el worker principal (no en el watcher)
            if os.environ.get('RUN_MAIN') == 'true':
                if not is_port_in_use(5001):
                    print("=> Iniciando servidor IA en segundo plano (puerto 5001)...")
                    base_dir = os.path.dirname(os.path.dirname(__file__))
                    script_path = os.path.join(base_dir, 'scripts', 'ia_server.py')
                    # Abrir el subproceso IA
                    subprocess.Popen([sys.executable, script_path])
                else:
                    print("=> Servidor IA ya está corriendo en el puerto 5001.")# trigger reload

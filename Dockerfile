# ════════════════════════════════════════════════════════════
#  SPORTS-MAX — Imagen Docker para producción (Render, Railway, etc.)
#  Proyecto Django: módulo "core", manage.py en la raíz del repositorio.
# ════════════════════════════════════════════════════════════
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Valor por defecto para pruebas rápidas; en Render define ALLOWED_HOSTS con tu dominio.
    ALLOWED_HOSTS=*

WORKDIR /app

# 1) Dependencias (capa cacheada: solo se reinstala si cambia requirements.txt)
COPY requirements.txt .
RUN pip install -r requirements.txt

# 2) Código del proyecto
COPY . .

# 3) Archivos estáticos (la SECRET_KEY real se inyecta en tiempo de ejecución)
RUN mkdir -p logs media \
    && SECRET_KEY=solo-para-collectstatic python manage.py collectstatic --noinput

EXPOSE 8000

# Render asigna el puerto en $PORT; si no existe usa 8000 (pruebas locales).
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn core.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 120"]

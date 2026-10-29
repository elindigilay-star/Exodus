"""Configuración central de EXODUS Contable.

Todo el proyecto (contabilidad, inventario, nómina y configuración) usa esta
misma configuración y una sola base de datos MySQL.

Los valores se pueden cambiar sin tocar el código con variables de entorno:

    EXODUS_DB_HOST       (por defecto 127.0.0.1)
    EXODUS_DB_PORT       (por defecto 3306)
    EXODUS_DB_USER       (por defecto root)
    EXODUS_DB_PASSWORD   (por defecto vacío)
    EXODUS_DB_NAME       (por defecto sistema_contable)
    EXODUS_SECRET_KEY    (si no se define, se genera en instance/secret_key)
    EXODUS_DEBUG         "1" para activar el depurador de Flask
    EXODUS_HOST          (por defecto 127.0.0.1)
    EXODUS_PORT          (por defecto 5000)
    EXODUS_DEMO          "0" para no crear usuarios de demostración
"""

import os
import secrets

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.environ.get("EXODUS_INSTANCE_DIR") or os.path.join(BASE_DIR, "instance")
RUTA_SECRET_KEY = os.path.join(INSTANCE_DIR, "secret_key")


def _booleano(nombre, defecto=False):
    """Lee una variable de entorno como booleano ("1", "true", "si", ...)."""
    valor = os.environ.get(nombre)
    if valor is None:
        return defecto
    return valor.strip().lower() in ("1", "true", "yes", "si", "sí", "on")


def clave_secreta():
    """Devuelve la clave de sesión sin dejarla escrita en el repositorio.

    Prioridad:
      1. Variable de entorno EXODUS_SECRET_KEY.
      2. Archivo instance/secret_key (se crea la primera vez).
    """
    desde_entorno = os.environ.get("EXODUS_SECRET_KEY")
    if desde_entorno:
        return desde_entorno

    os.makedirs(INSTANCE_DIR, exist_ok=True)
    if os.path.exists(RUTA_SECRET_KEY):
        with open(RUTA_SECRET_KEY, encoding="utf-8") as archivo:
            clave = archivo.read().strip()
        if clave:
            return clave

    clave = secrets.token_hex(32)
    with open(RUTA_SECRET_KEY, "w", encoding="utf-8") as archivo:
        archivo.write(clave)
    return clave


DB_HOST = os.environ.get("EXODUS_DB_HOST", "127.0.0.1")
DB_PORT = int(os.environ.get("EXODUS_DB_PORT", "3306"))
DB_USER = os.environ.get("EXODUS_DB_USER", "root")
DB_PASSWORD = os.environ.get("EXODUS_DB_PASSWORD", "")
DB_NAME = os.environ.get("EXODUS_DB_NAME", "sistema_contable")

DB_CONFIG = {
    "host": DB_HOST,
    "port": DB_PORT,
    "user": DB_USER,
    "password": DB_PASSWORD,
    "database": DB_NAME,
    "charset": "utf8mb4",
}

DEBUG = _booleano("EXODUS_DEBUG", False)
HOST = os.environ.get("EXODUS_HOST", "127.0.0.1")
PORT = int(os.environ.get("EXODUS_PORT", "5000"))
DEMO = _booleano("EXODUS_DEMO", True)

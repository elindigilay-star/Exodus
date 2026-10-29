"""Conexión única a MySQL para todos los módulos de EXODUS Contable."""

import pymysql
from pymysql.cursors import DictCursor

from config import DB_CONFIG


def obtener_conexion():
    """Devuelve una conexión nueva usando la configuración central."""
    return pymysql.connect(cursorclass=DictCursor, **DB_CONFIG)

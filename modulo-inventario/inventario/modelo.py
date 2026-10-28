"""Modelo de datos del módulo de inventario.

Usa la misma conexión MySQL (`database.connection.obtener_conexion`)
que el resto de Modulo-contable.
"""

from database.connection import obtener_conexion


# ---------------------------------------------------------------
# Etiquetas (clasifican productos y definen impuestos/tasas)
# ---------------------------------------------------------------

def listar_etiquetas():
    """Devuelve todas las etiquetas ordenadas por tipo y nombre."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM etiquetas ORDER BY tipo, nombre")
            return cursor.fetchall()
    finally:
        conexion.close()


def obtener_etiqueta(id_etiqueta):
    """Devuelve una etiqueta por su ID o None si no existe."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM etiquetas WHERE id = %s", (id_etiqueta,))
            return cursor.fetchone()
    finally:
        conexion.close()


def crear_etiqueta(nombre, tipo, porcentaje):
    """Crea una etiqueta. Lanza pymysql.err.IntegrityError si el nombre ya existe."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "INSERT INTO etiquetas (nombre, tipo, porcentaje) VALUES (%s, %s, %s)",
                (nombre, tipo, porcentaje),
            )
        conexion.commit()
    finally:
        conexion.close()


def actualizar_etiqueta(id_etiqueta, nombre, tipo, porcentaje):
    """Actualiza una etiqueta. Lanza pymysql.err.IntegrityError si el nombre ya existe."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "UPDATE etiquetas SET nombre = %s, tipo = %s, porcentaje = %s WHERE id = %s",
                (nombre, tipo, porcentaje, id_etiqueta),
            )
        conexion.commit()
    finally:
        conexion.close()


def eliminar_etiqueta(id_etiqueta):
    """Elimina una etiqueta por su ID."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("DELETE FROM etiquetas WHERE id = %s", (id_etiqueta,))
        conexion.commit()
    finally:
        conexion.close()
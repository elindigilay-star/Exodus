from database.connection import obtener_conexion


def obtener_producto_por_id(id_producto):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT * FROM productos WHERE id_producto = %s"
            cursor.execute(sql, (id_producto,))
            return cursor.fetchone()
    finally:
        conexion.close()

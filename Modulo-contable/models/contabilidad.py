from database.connection import obtener_conexion

def insertar_gasto(descripcion, monto, id_usuario):
    """Guarda un gasto deducible en la base de datos."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                INSERT INTO gastos_deducibles (descripcion, monto, id_usuario, fecha)
                VALUES (%s, %s, %s, NOW())
            """
            cursor.execute(sql, (descripcion, monto, id_usuario))
            conexion.commit()
            return cursor.lastrowid
    finally:
        conexion.close()

def obtener_total_gastos(fecha_inicio=None, fecha_fin=None):
    """Obtiene la suma total de gastos deducibles en un periodo."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT COALESCE(SUM(monto), 0) AS total FROM gastos_deducibles"
            params = []
            if fecha_inicio and fecha_fin:
                sql += " WHERE fecha BETWEEN %s AND %s"
                params.extend([fecha_inicio, fecha_fin])
            
            cursor.execute(sql, params)
            resultado = cursor.fetchone()
            return float(resultado['total']) if resultado else 0.0
    finally:
        conexion.close()
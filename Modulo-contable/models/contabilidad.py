from database.connection import obtener_conexion

def insertar_gasto(descripcion, monto, id_usuario, categoria=None, tercero=None,
                   nit=None, numero_documento=None, fecha=None):
    """Guarda un gasto deducible en la base de datos."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                INSERT INTO gastos_deducibles
                    (descripcion, monto, id_usuario, fecha, categoria, tercero, nit, numero_documento)
                VALUES (%s, %s, %s, COALESCE(%s, NOW()), %s, %s, %s, %s)
            """
            cursor.execute(sql, (descripcion, monto, id_usuario, fecha,
                                 categoria, tercero, nit, numero_documento))
            conexion.commit()
            return cursor.lastrowid
    finally:
        conexion.close()

def obtener_total_gastos(fecha_inicio=None, fecha_fin=None):
    """Obtiene la suma total de gastos deducibles activos en un periodo."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT COALESCE(SUM(monto), 0) AS total FROM gastos_deducibles WHERE estado_gasto = 'ACTIVO'"
            params = []
            if fecha_inicio and fecha_fin:
                sql += " AND fecha BETWEEN %s AND %s"
                params.extend([fecha_inicio, fecha_fin])
            
            cursor.execute(sql, params)
            resultado = cursor.fetchone()
            return float(resultado['total']) if resultado else 0.0
    finally:
        conexion.close()

def listar_gastos(fecha_inicio=None, fecha_fin=None, estado_gasto='ACTIVO'):
    """Lista los gastos deducibles con sus metadatos, opcionalmente filtrados por periodo y estado."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT g.id_gasto, g.descripcion, g.monto, g.fecha,
                       g.categoria, g.tercero, g.nit, g.numero_documento,
                       g.estado_gasto, u.nombre AS usuario
                FROM gastos_deducibles g
                JOIN usuarios u ON u.id_usuario = g.id_usuario
                WHERE g.estado_gasto = %s
            """
            params = [estado_gasto]
            if fecha_inicio and fecha_fin:
                sql += " AND g.fecha BETWEEN %s AND %s"
                params.extend([fecha_inicio, fecha_fin])
            sql += " ORDER BY g.fecha DESC, g.id_gasto DESC"

            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conexion.close()

def obtener_gasto(id_gasto):
    """Obtiene un gasto deducible por su ID."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT g.id_gasto, g.descripcion, g.monto, g.fecha,
                       g.categoria, g.tercero, g.nit, g.numero_documento,
                       g.estado_gasto, u.nombre AS usuario
                FROM gastos_deducibles g
                JOIN usuarios u ON u.id_usuario = g.id_usuario
                WHERE g.id_gasto = %s
                """,
                (id_gasto,),
            )
            return cursor.fetchone()
    finally:
        conexion.close()

def actualizar_gasto(id_gasto, descripcion, monto, categoria=None, tercero=None,
                     nit=None, numero_documento=None, fecha=None):
    """Actualiza un gasto deducible existente."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                UPDATE gastos_deducibles
                SET descripcion = %s, monto = %s, categoria = %s, tercero = %s,
                    nit = %s, numero_documento = %s, fecha = COALESCE(%s, fecha)
                WHERE id_gasto = %s AND estado_gasto = 'ACTIVO'
                """,
                (descripcion, monto, categoria, tercero, nit, numero_documento, fecha, id_gasto),
            )
            conexion.commit()
            return cursor.rowcount
    finally:
        conexion.close()

def anular_gasto(id_gasto):
    """Anula lógicamente un gasto deducible (borrado lógico)."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "UPDATE gastos_deducibles SET estado_gasto = 'ANULADO' WHERE id_gasto = %s",
                (id_gasto,),
            )
            conexion.commit()
            return cursor.rowcount
    finally:
        conexion.close()
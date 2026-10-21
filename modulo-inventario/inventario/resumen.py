from database.connection import obtener_conexion


def _rango(campo, fecha_inicio, fecha_fin):
    """Devuelve (cláusula SQL, parámetros) para filtrar por periodo."""
    if fecha_inicio and fecha_fin:
        return f" AND {campo} BETWEEN %s AND %s", [fecha_inicio, fecha_fin]
    return "", []


def obtener_resumen_inventario(fecha_inicio=None, fecha_fin=None):
    """
    Datos del módulo de inventario que consume contabilidad:
      - ingresos_totales / costo_ventas: ventas (tabla ventas_inventario).
      - compras: entradas de mercancía valoradas a su costo (salida de caja).
      - costo_ventas_manuales: costo de ventas que no tienen movimiento de stock
        (registros históricos); se tratan como mercancía ya pagada.
      - perdidas: mermas, salidas y ajustes negativos (gasto sin salida de caja).
    """
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            filtro_v, params_v = _rango('v.fecha', fecha_inicio, fecha_fin)
            cursor.execute(
                f"""
                SELECT COALESCE(SUM(v.monto_total), 0) AS ingresos_totales,
                       COALESCE(SUM(v.costo_ventas), 0) AS costo_ventas
                  FROM ventas_inventario v
                 WHERE 1 = 1 {filtro_v}
                """,
                params_v,
            )
            ventas = cursor.fetchone()

            resultado = {
                'ingresos_totales': float(ventas['ingresos_totales']),
                'costo_ventas': float(ventas['costo_ventas']),
                'compras': 0.0,
                'costo_ventas_manuales': float(ventas['costo_ventas']),
                'perdidas': 0.0,
            }

            # Las tablas de movimientos pueden no existir todavía: se tolera.
            try:
                cursor.execute(
                    f"""
                    SELECT COALESCE(SUM(v.costo_ventas), 0) AS costo
                      FROM ventas_inventario v
                     WHERE v.id_venta NOT IN (
                               SELECT id_venta FROM movimientos_inventario WHERE id_venta IS NOT NULL)
                           {filtro_v}
                    """,
                    params_v,
                )
                resultado['costo_ventas_manuales'] = float(cursor.fetchone()['costo'])

                filtro_m, params_m = _rango('fecha', fecha_inicio, fecha_fin)
                cursor.execute(
                    f"""
                    SELECT COALESCE(SUM(CASE WHEN tipo = 'ENTRADA' THEN cantidad * costo_unitario END), 0) AS compras,
                           COALESCE(SUM(CASE WHEN tipo IN ('SALIDA', 'AJUSTE') THEN -cantidad * costo_unitario END), 0) AS perdidas
                      FROM movimientos_inventario
                     WHERE 1 = 1 {filtro_m}
                    """,
                    params_m,
                )
                fila = cursor.fetchone()
                resultado['compras'] = float(fila['compras'])
                resultado['perdidas'] = float(fila['perdidas'])
            except Exception as error:
                print(f"AVISO: movimientos de inventario no disponibles: {error}")
            return resultado
    finally:
        conexion.close()


def obtener_posicion_inventario():
    """Valor actual de la mercancía en bodega (a costo promedio) e indicadores de stock."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(SUM(stock_actual * costo_promedio), 0) AS valor_inventario,
                       COUNT(*) AS productos_activos,
                       COALESCE(SUM(stock_actual <= stock_minimo), 0) AS bajo_stock
                  FROM productos
                 WHERE activo = 1
                """
            )
            fila = cursor.fetchone()
            return {
                'valor_inventario': float(fila['valor_inventario']),
                'productos_activos': int(fila['productos_activos']),
                'bajo_stock': int(fila['bajo_stock']),
            }
    finally:
        conexion.close()

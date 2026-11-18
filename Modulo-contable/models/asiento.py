"""Modelo de acceso a datos para asientos contables y movimientos (doble entrada)."""

from database.connection import obtener_conexion


def listar_asientos(fecha_inicio=None, fecha_fin=None, estado=None):
    """Lista asientos contables con totales de debe y haber."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT a.id_asiento, a.numero_asiento, a.fecha, a.descripcion,
                       a.referencia, a.estado, a.id_usuario, u.nombre AS usuario,
                       a.fecha_creacion, a.fecha_contabilizacion,
                       COALESCE(SUM(m.debe), 0) AS total_debe,
                       COALESCE(SUM(m.haber), 0) AS total_haber
                FROM asientos_contables a
                JOIN usuarios u ON u.id_usuario = a.id_usuario
                LEFT JOIN movimientos_contables m ON m.id_asiento = a.id_asiento
                WHERE 1 = 1
            """
            params = []
            if fecha_inicio and fecha_fin:
                sql += " AND a.fecha BETWEEN %s AND %s"
                params.extend([fecha_inicio, fecha_fin])
            if estado:
                sql += " AND a.estado = %s"
                params.append(estado)
            sql += " GROUP BY a.id_asiento ORDER BY a.fecha DESC, a.id_asiento DESC"
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conexion.close()


def obtener_asiento(id_asiento):
    """Obtiene un asiento contable con todos sus movimientos."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT a.id_asiento, a.numero_asiento, a.fecha, a.descripcion,
                       a.referencia, a.estado, a.id_usuario, u.nombre AS usuario,
                       a.fecha_creacion, a.fecha_contabilizacion
                FROM asientos_contables a
                JOIN usuarios u ON u.id_usuario = a.id_usuario
                WHERE a.id_asiento = %s
                """,
                (id_asiento,),
            )
            asiento = cursor.fetchone()
            if not asiento:
                return None

            cursor.execute(
                """
                SELECT m.id_movimiento, m.id_asiento, m.id_cuenta,
                       pc.codigo AS codigo_cuenta, pc.nombre AS nombre_cuenta,
                       pc.naturaleza, m.debe, m.haber, m.detalle,
                       m.base_gravable, m.valor_iva, m.tipo_iva
                FROM movimientos_contables m
                JOIN plan_cuentas pc ON pc.id_cuenta = m.id_cuenta
                WHERE m.id_asiento = %s
                ORDER BY m.id_movimiento
                """,
                (id_asiento,),
            )
            movimientos = cursor.fetchall()
            asiento["movimientos"] = movimientos
            return asiento
    finally:
        conexion.close()


def crear_asiento(numero_asiento, fecha, descripcion, id_usuario, referencia=None,
                  movimientos=None):
    """
    Crea un asiento contable con sus movimientos (doble entrada).

    `movimientos` es una lista de diccionarios con las claves:
      id_cuenta, debe, haber, detalle, base_gravable, valor_iva, tipo_iva

    Regla de negocio: SUM(debe) == SUM(haber). Si no, lanza ValueError.
    """
    if movimientos is None:
        movimientos = []

    total_debe = sum(float(m.get("debe", 0) or 0) for m in movimientos)
    total_haber = sum(float(m.get("haber", 0) or 0) for m in movimientos)

    if abs(total_debe - total_haber) > 0.001:
        raise ValueError(
            f"El asiento no está cuadrado: debe={total_debe:,.2f}, "
            f"haber={total_haber:,.2f}. Diferencia={abs(total_debe - total_haber):,.2f}"
        )

    if len(movimientos) < 2:
        raise ValueError("Un asiento contable debe tener al menos 2 movimientos (debe y haber).")

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Validar número de asiento único
            cursor.execute(
                "SELECT id_asiento FROM asientos_contables WHERE numero_asiento = %s",
                (numero_asiento,),
            )
            if cursor.fetchone():
                raise ValueError(f"Ya existe un asiento con el número {numero_asiento}.")

            # Insertar cabecera del asiento
            cursor.execute(
                """
                INSERT INTO asientos_contables
                    (numero_asiento, fecha, descripcion, referencia, estado, id_usuario)
                VALUES (%s, %s, %s, %s, 'BORRADOR', %s)
                """,
                (numero_asiento, fecha, descripcion, referencia, id_usuario),
            )
            id_asiento = cursor.lastrowid

            # Insertar movimientos
            for m in movimientos:
                cursor.execute(
                    """
                    INSERT INTO movimientos_contables
                        (id_asiento, id_cuenta, debe, haber, detalle,
                         base_gravable, valor_iva, tipo_iva)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        id_asiento,
                        m["id_cuenta"],
                        float(m.get("debe", 0) or 0),
                        float(m.get("haber", 0) or 0),
                        m.get("detalle"),
                        float(m.get("base_gravable", 0) or 0),
                        float(m.get("valor_iva", 0) or 0),
                        m.get("tipo_iva", "excluido"),
                    ),
                )

            conexion.commit()
            return id_asiento
    finally:
        conexion.close()


def actualizar_asiento(id_asiento, fecha, descripcion, referencia=None,
                       movimientos=None):
    """Actualiza un asiento en estado BORRADOR y sus movimientos."""
    if movimientos is None:
        movimientos = []

    total_debe = sum(float(m.get("debe", 0) or 0) for m in movimientos)
    total_haber = sum(float(m.get("haber", 0) or 0) for m in movimientos)

    if abs(total_debe - total_haber) > 0.001:
        raise ValueError(
            f"El asiento no está cuadrado: debe={total_debe:,.2f}, "
            f"haber={total_haber:,.2f}."
        )

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT estado FROM asientos_contables WHERE id_asiento = %s",
                (id_asiento,),
            )
            fila = cursor.fetchone()
            if not fila:
                raise ValueError("El asiento contable no existe.")
            if fila["estado"] != "BORRADOR":
                raise ValueError("Solo se pueden editar asientos en estado BORRADOR.")

            cursor.execute(
                """
                UPDATE asientos_contables
                SET fecha = %s, descripcion = %s, referencia = %s
                WHERE id_asiento = %s
                """,
                (fecha, descripcion, referencia, id_asiento),
            )

            # Borrar movimientos existentes y volver a insertar
            cursor.execute(
                "DELETE FROM movimientos_contables WHERE id_asiento = %s",
                (id_asiento,),
            )
            for m in movimientos:
                cursor.execute(
                    """
                    INSERT INTO movimientos_contables
                        (id_asiento, id_cuenta, debe, haber, detalle,
                         base_gravable, valor_iva, tipo_iva)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        id_asiento,
                        m["id_cuenta"],
                        float(m.get("debe", 0) or 0),
                        float(m.get("haber", 0) or 0),
                        m.get("detalle"),
                        float(m.get("base_gravable", 0) or 0),
                        float(m.get("valor_iva", 0) or 0),
                        m.get("tipo_iva", "excluido"),
                    ),
                )

            conexion.commit()
            return cursor.rowcount
    finally:
        conexion.close()


def contabilizar_asiento(id_asiento):
    """Cambia el estado de un asiento de BORRADOR a CONTABLE."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT estado FROM asientos_contables WHERE id_asiento = %s",
                (id_asiento,),
            )
            fila = cursor.fetchone()
            if not fila:
                raise ValueError("El asiento contable no existe.")
            if fila["estado"] != "BORRADOR":
                raise ValueError("Solo se pueden contabilizar asientos en estado BORRADOR.")

            # Validar que esté cuadrado antes de contabilizar
            cursor.execute(
                """
                SELECT COALESCE(SUM(debe), 0) AS total_debe,
                       COALESCE(SUM(haber), 0) AS total_haber
                FROM movimientos_contables WHERE id_asiento = %s
                """,
                (id_asiento,),
            )
            totales = cursor.fetchone()
            if abs(float(totales["total_debe"]) - float(totales["total_haber"])) > 0.001:
                raise ValueError("No se puede contabilizar: el asiento no está cuadrado.")

            cursor.execute(
                """
                UPDATE asientos_contables
                SET estado = 'CONTABLE', fecha_contabilizacion = NOW()
                WHERE id_asiento = %s AND estado = 'BORRADOR'
                """,
                (id_asiento,),
            )
            conexion.commit()
            return cursor.rowcount
    finally:
        conexion.close()


def anular_asiento(id_asiento):
    """Anula un asiento contable (cambia estado a ANULADO)."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT estado FROM asientos_contables WHERE id_asiento = %s",
                (id_asiento,),
            )
            fila = cursor.fetchone()
            if not fila:
                raise ValueError("El asiento contable no existe.")
            if fila["estado"] == "ANULADO":
                raise ValueError("El asiento ya está anulado.")

            cursor.execute(
                """
                UPDATE asientos_contables
                SET estado = 'ANULADO'
                WHERE id_asiento = %s
                """,
                (id_asiento,),
            )
            conexion.commit()
            return cursor.rowcount
    finally:
        conexion.close()


def obtener_saldo_cuenta(id_cuenta, fecha_inicio=None, fecha_fin=None):
    """Calcula el saldo acumulado (debe - haber) de una cuenta en un periodo."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT COALESCE(SUM(m.debe), 0) AS total_debe,
                       COALESCE(SUM(m.haber), 0) AS total_haber
                FROM movimientos_contables m
                JOIN asientos_contables a ON a.id_asiento = m.id_asiento
                WHERE m.id_cuenta = %s AND a.estado = 'CONTABLE'
            """
            params = [id_cuenta]
            if fecha_inicio and fecha_fin:
                sql += " AND a.fecha BETWEEN %s AND %s"
                params.extend([fecha_inicio, fecha_fin])
            cursor.execute(sql, params)
            fila = cursor.fetchone()
            debe = float(fila["total_debe"] or 0)
            haber = float(fila["total_haber"] or 0)
            return {
                "total_debe": debe,
                "total_haber": haber,
                "saldo": debe - haber,
            }
    finally:
        conexion.close()
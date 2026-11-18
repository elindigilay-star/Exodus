"""Modelo de acceso a datos para el Plan de Cuentas Contables."""

from database.connection import obtener_conexion


def listar_cuentas(activo=None, solo_movimiento=False):
    """Retorna el plan de cuentas con jerarquía (padre incluido)."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT c.id_cuenta, c.codigo, c.nombre, c.tipo, c.naturaleza,
                       c.cuenta_padre_id, c.nivel, c.permite_movimiento, c.activo,
                       p.codigo AS codigo_padre, p.nombre AS nombre_padre
                FROM plan_cuentas c
                LEFT JOIN plan_cuentas p ON p.id_cuenta = c.cuenta_padre_id
                WHERE 1 = 1
            """
            params = []
            if activo is not None:
                sql += " AND c.activo = %s"
                params.append(int(activo))
            if solo_movimiento:
                sql += " AND c.permite_movimiento = 1"
            sql += " ORDER BY c.codigo"
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conexion.close()


def obtener_cuenta(id_cuenta):
    """Obtiene una cuenta contable por su ID."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT c.*, p.codigo AS codigo_padre, p.nombre AS nombre_padre
                FROM plan_cuentas c
                LEFT JOIN plan_cuentas p ON p.id_cuenta = c.cuenta_padre_id
                WHERE c.id_cuenta = %s
                """,
                (id_cuenta,),
            )
            return cursor.fetchone()
    finally:
        conexion.close()


def obtener_cuenta_por_codigo(codigo):
    """Obtiene una cuenta contable por su código."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM plan_cuentas WHERE codigo = %s",
                (codigo,),
            )
            return cursor.fetchone()
    finally:
        conexion.close()


def crear_cuenta(codigo, nombre, tipo, naturaleza, cuenta_padre_id=None,
                 nivel=1, permite_movimiento=1, activo=1):
    """Crea una nueva cuenta contable."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Validar que el código no exista
            cursor.execute("SELECT id_cuenta FROM plan_cuentas WHERE codigo = %s", (codigo,))
            if cursor.fetchone():
                raise ValueError(f"Ya existe una cuenta con el código {codigo}.")

            # Validar cuenta padre si se especifica
            if cuenta_padre_id:
                cursor.execute("SELECT nivel FROM plan_cuentas WHERE id_cuenta = %s", (cuenta_padre_id,))
                padre = cursor.fetchone()
                if not padre:
                    raise ValueError("La cuenta padre especificada no existe.")
                if padre["nivel"] >= 3:
                    raise ValueError("No se pueden crear cuentas bajo una cuenta de nivel 3.")

            cursor.execute(
                """
                INSERT INTO plan_cuentas
                    (codigo, nombre, tipo, naturaleza, cuenta_padre_id, nivel,
                     permite_movimiento, activo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (codigo, nombre, tipo, naturaleza, cuenta_padre_id, nivel,
                 int(permite_movimiento), int(activo)),
            )
            conexion.commit()
            return cursor.lastrowid
    finally:
        conexion.close()


def actualizar_cuenta(id_cuenta, codigo, nombre, tipo, naturaleza, cuenta_padre_id=None,
                      nivel=1, permite_movimiento=1, activo=1):
    """Actualiza una cuenta contable existente."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id_cuenta FROM plan_cuentas WHERE id_cuenta = %s", (id_cuenta,))
            if not cursor.fetchone():
                raise ValueError("La cuenta contable no existe.")

            # Validar código único (excluyendo la propia cuenta)
            cursor.execute(
                "SELECT id_cuenta FROM plan_cuentas WHERE codigo = %s AND id_cuenta <> %s",
                (codigo, id_cuenta),
            )
            if cursor.fetchone():
                raise ValueError(f"Ya existe otra cuenta con el código {codigo}.")

            # Validar cuenta padre
            if cuenta_padre_id:
                cursor.execute("SELECT nivel FROM plan_cuentas WHERE id_cuenta = %s", (cuenta_padre_id,))
                padre = cursor.fetchone()
                if not padre:
                    raise ValueError("La cuenta padre especificada no existe.")
                if padre["nivel"] >= 3:
                    raise ValueError("No se pueden crear cuentas bajo una cuenta de nivel 3.")
                # No permitir que una cuenta sea su propio padre
                if cuenta_padre_id == id_cuenta:
                    raise ValueError("Una cuenta no puede ser su propia padre.")

            cursor.execute(
                """
                UPDATE plan_cuentas
                SET codigo = %s, nombre = %s, tipo = %s, naturaleza = %s,
                    cuenta_padre_id = %s, nivel = %s, permite_movimiento = %s, activo = %s
                WHERE id_cuenta = %s
                """,
                (codigo, nombre, tipo, naturaleza, cuenta_padre_id, nivel,
                 int(permite_movimiento), int(activo), id_cuenta),
            )
            conexion.commit()
            return cursor.rowcount
    finally:
        conexion.close()


def eliminar_cuenta(id_cuenta):
    """Elimina lógicamente una cuenta contable (activo = 0)."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id_cuenta FROM plan_cuentas WHERE id_cuenta = %s", (id_cuenta,))
            if not cursor.fetchone():
                raise ValueError("La cuenta contable no existe.")

            # Verificar que no tenga movimientos contables asociados
            cursor.execute(
                "SELECT COUNT(*) AS total FROM movimientos_contables WHERE id_cuenta = %s",
                (id_cuenta,),
            )
            if cursor.fetchone()["total"] > 0:
                raise ValueError(
                    "No se puede eliminar: la cuenta tiene movimientos contables asociados."
                )

            cursor.execute(
                "UPDATE plan_cuentas SET activo = 0 WHERE id_cuenta = %s",
                (id_cuenta,),
            )
            conexion.commit()
            return cursor.rowcount
    finally:
        conexion.close()


def obtener_arbol_cuentas():
    """Retorna el plan de cuentas organizado como árbol (padre -> hijos)."""
    cuentas = listar_cuentas(activo=1)
    por_id = {c["id_cuenta"]: dict(c, hijos=[]) for c in cuentas}
    raices = []
    for c in cuentas:
        c_dict = por_id[c["id_cuenta"]]
        if c["cuenta_padre_id"] and c["cuenta_padre_id"] in por_id:
            por_id[c["cuenta_padre_id"]]["hijos"].append(c_dict)
        else:
            raices.append(c_dict)
    return raices
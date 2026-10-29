from werkzeug.security import generate_password_hash

from database.connection import obtener_conexion


def obtener_usuario_por_id(id_usuario):
    """Obtiene la información y rol de un usuario."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = (
                "SELECT id_usuario, nombre, email, rol, activo "
                "FROM usuarios WHERE id_usuario = %s"
            )
            cursor.execute(sql, (id_usuario,))
            return cursor.fetchone()
    finally:
        conexion.close()


def obtener_usuario_por_usuario(usuario):
    """Obtiene un usuario (incluida su clave cifrada) para iniciar sesión."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT id_usuario, usuario, nombre, email, rol, clave_hash, activo
                FROM usuarios
                WHERE usuario = %s
            """
            cursor.execute(sql, (usuario,))
            return cursor.fetchone()
    finally:
        conexion.close()


def listar_usuarios():
    """Retorna todos los usuarios registrados."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT id_usuario, usuario, nombre, email, rol, activo
                FROM usuarios
                ORDER BY id_usuario
            """
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        conexion.close()


def obtener_usuario_completo(id_usuario):
    """Obtiene un usuario con todos los campos usados en la gestión."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id_usuario, usuario, nombre, email, rol, activo
                FROM usuarios WHERE id_usuario = %s
                """,
                (id_usuario,),
            )
            return cursor.fetchone()
    finally:
        conexion.close()


def existe_usuario(usuario, excluir_id=None):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT id_usuario FROM usuarios WHERE usuario = %s"
            params = [usuario]
            if excluir_id is not None:
                sql += " AND id_usuario <> %s"
                params.append(excluir_id)
            cursor.execute(sql, params)
            return cursor.fetchone() is not None
    finally:
        conexion.close()


def existe_email(email, excluir_id=None):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT id_usuario FROM usuarios WHERE email = %s"
            params = [email]
            if excluir_id is not None:
                sql += " AND id_usuario <> %s"
                params.append(excluir_id)
            cursor.execute(sql, params)
            return cursor.fetchone() is not None
    finally:
        conexion.close()


def contar_admins_activos(excluir_id=None):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = (
                "SELECT COUNT(*) AS total FROM usuarios "
                "WHERE LOWER(rol) = 'administrador' AND activo = 1"
            )
            params = []
            if excluir_id is not None:
                sql += " AND id_usuario <> %s"
                params.append(excluir_id)
            cursor.execute(sql, params)
            return cursor.fetchone()["total"]
    finally:
        conexion.close()


def crear_usuario(nombre, usuario, email, rol, clave, activo=True):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO usuarios (usuario, nombre, email, rol, clave_hash, activo)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (usuario, nombre, email, rol, generate_password_hash(clave), int(activo)),
            )
            conexion.commit()
            return cursor.lastrowid
    finally:
        conexion.close()


def actualizar_usuario(id_usuario, nombre, rol, activo, clave=None):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            if clave:
                cursor.execute(
                    """
                    UPDATE usuarios
                    SET nombre = %s, rol = %s, activo = %s, clave_hash = %s
                    WHERE id_usuario = %s
                    """,
                    (nombre, rol, int(activo), generate_password_hash(clave), id_usuario),
                )
            else:
                cursor.execute(
                    "UPDATE usuarios SET nombre = %s, rol = %s, activo = %s WHERE id_usuario = %s",
                    (nombre, rol, int(activo), id_usuario),
                )
            conexion.commit()
            return cursor.rowcount
    finally:
        conexion.close()


def eliminar_usuario(id_usuario):
    """Borrado lógico: el usuario queda inactivo y no puede iniciar sesión."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "UPDATE usuarios SET activo = 0 WHERE id_usuario = %s",
                (id_usuario,),
            )
            conexion.commit()
            return cursor.rowcount
    finally:
        conexion.close()


# ---------------------------------------------------------------
# Intentos de inicio de sesión (persistidos, no en memoria)
# ---------------------------------------------------------------

def segundos_bloqueado(usuario, ip):
    """Segundos que le quedan de bloqueo a (usuario, ip); 0 si no está bloqueado."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT TIMESTAMPDIFF(SECOND, NOW(), bloqueado_hasta) AS restante
                FROM intentos_login
                WHERE usuario = %s AND ip = %s AND bloqueado_hasta > NOW()
                """,
                (usuario, ip),
            )
            fila = cursor.fetchone()
            return max(int(fila["restante"]), 0) if fila else 0
    finally:
        conexion.close()


def registrar_intento_fallido(usuario, ip, max_intentos, segundos_bloqueo):
    """Suma un fallo y bloquea la combinación usuario/IP al llegar al máximo."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT fallos,
                       (bloqueado_hasta IS NOT NULL AND bloqueado_hasta > NOW()) AS vigente
                FROM intentos_login
                WHERE usuario = %s AND ip = %s
                FOR UPDATE
                """,
                (usuario, ip),
            )
            fila = cursor.fetchone()

            fallos = 0
            if fila and not fila["vigente"]:
                fallos = int(fila["fallos"])
            fallos += 1

            bloqueado_hasta = None
            if fallos >= max_intentos:
                cursor.execute("SELECT DATE_ADD(NOW(), INTERVAL %s SECOND) AS hasta",
                               (segundos_bloqueo,))
                bloqueado_hasta = cursor.fetchone()["hasta"]
                fallos = 0

            cursor.execute(
                """
                INSERT INTO intentos_login (usuario, ip, fallos, bloqueado_hasta)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    fallos = VALUES(fallos),
                    bloqueado_hasta = VALUES(bloqueado_hasta)
                """,
                (usuario, ip, fallos, bloqueado_hasta),
            )
        conexion.commit()
    finally:
        conexion.close()


def limpiar_intentos(usuario, ip):
    """Borra el historial de fallos después de un inicio de sesión correcto."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "DELETE FROM intentos_login WHERE usuario = %s AND ip = %s",
                (usuario, ip),
            )
        conexion.commit()
    finally:
        conexion.close()

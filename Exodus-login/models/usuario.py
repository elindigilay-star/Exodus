from werkzeug.security import generate_password_hash

from database.connection import obtener_conexion


def obtener_usuario_por_id(id_usuario):
    """Obtiene la información y rol de un usuario."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT id_usuario, nombre, email, rol FROM usuarios WHERE id_usuario = %s"
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
            sql = "SELECT COUNT(*) AS total FROM usuarios WHERE LOWER(rol) = 'administrador' AND activo = 1"
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

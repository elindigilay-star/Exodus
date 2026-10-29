"""Acceso a datos del módulo de configuración.

Tablas creadas/consultadas en la base `sistema_contable`:
  - etiquetas, parametros          (catálogo contable)
  - roles, permisos, rol_permiso   (control de acceso)

Los usuarios NO se manejan aquí: se usan los de `models.usuario`
(la misma tabla `usuarios` del inicio de sesión de Modulo-contable).
"""

from database.connection import obtener_conexion


# ---------------------------------------------------------------
# Etiquetas
# ---------------------------------------------------------------

def listar_etiquetas():
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM etiquetas ORDER BY tipo, nombre")
            return cursor.fetchall()
    finally:
        conexion.close()


def obtener_etiqueta(id_etiqueta):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM etiquetas WHERE id = %s", (id_etiqueta,))
            return cursor.fetchone()
    finally:
        conexion.close()


def crear_etiqueta(nombre, tipo, porcentaje):
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
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("DELETE FROM etiquetas WHERE id = %s", (id_etiqueta,))
        conexion.commit()
    finally:
        conexion.close()


# ---------------------------------------------------------------
# Parámetros
# ---------------------------------------------------------------

def listar_parametros():
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT p.*, e.nombre AS etiqueta_nombre
                FROM parametros p
                JOIN etiquetas e ON e.id = p.etiqueta_id
                ORDER BY p.nombre
                """
            )
            return cursor.fetchall()
    finally:
        conexion.close()


def obtener_parametro(id_parametro):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM parametros WHERE id = %s", (id_parametro,))
            return cursor.fetchone()
    finally:
        conexion.close()


def crear_parametro(nombre, etiqueta_id, valor, descripcion):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO parametros (nombre, etiqueta_id, valor, descripcion)
                VALUES (%s, %s, %s, %s)
                """,
                (nombre, etiqueta_id, valor, descripcion),
            )
        conexion.commit()
    finally:
        conexion.close()


def actualizar_parametro(id_parametro, nombre, etiqueta_id, valor, descripcion):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                UPDATE parametros
                SET nombre = %s, etiqueta_id = %s, valor = %s, descripcion = %s
                WHERE id = %s
                """,
                (nombre, etiqueta_id, valor, descripcion, id_parametro),
            )
        conexion.commit()
    finally:
        conexion.close()


def eliminar_parametro(id_parametro):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("DELETE FROM parametros WHERE id = %s", (id_parametro,))
        conexion.commit()
    finally:
        conexion.close()


# ---------------------------------------------------------------
# Roles y permisos
# ---------------------------------------------------------------

def listar_roles():
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM roles ORDER BY nombre")
            return cursor.fetchall()
    finally:
        conexion.close()


def obtener_rol(id_rol):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM roles WHERE id = %s", (id_rol,))
            return cursor.fetchone()
    finally:
        conexion.close()


def listar_permisos():
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM permisos ORDER BY nombre")
            return cursor.fetchall()
    finally:
        conexion.close()


def listar_permisos_de_rol(id_rol):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT p.id, p.nombre, p.descripcion
                FROM permisos p
                JOIN rol_permiso rp ON rp.permiso_id = p.id
                WHERE rp.rol_id = %s
                ORDER BY p.nombre
                """,
                (id_rol,),
            )
            return cursor.fetchall()
    finally:
        conexion.close()


def listar_roles_con_permisos():
    roles = listar_roles()
    for rol in roles:
        permisos = listar_permisos_de_rol(rol['id'])
        rol['permisos'] = permisos
        rol['permisos_ids'] = [p['id'] for p in permisos]
    return roles


def _asignar_permisos(cursor, id_rol, permisos_ids):
    cursor.execute("DELETE FROM rol_permiso WHERE rol_id = %s", (id_rol,))
    if permisos_ids:
        cursor.executemany(
            "INSERT INTO rol_permiso (rol_id, permiso_id) VALUES (%s, %s)",
            [(id_rol, p) for p in permisos_ids],
        )


def crear_rol(nombre, descripcion, permisos_ids):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "INSERT INTO roles (nombre, descripcion) VALUES (%s, %s)",
                (nombre, descripcion),
            )
            _asignar_permisos(cursor, cursor.lastrowid, permisos_ids)
        conexion.commit()
    finally:
        conexion.close()


def actualizar_rol(id_rol, nombre, descripcion, permisos_ids):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "UPDATE roles SET nombre = %s, descripcion = %s WHERE id = %s",
                (nombre, descripcion, id_rol),
            )
            _asignar_permisos(cursor, id_rol, permisos_ids)
        conexion.commit()
    finally:
        conexion.close()


def eliminar_rol(id_rol):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("DELETE FROM roles WHERE id = %s", (id_rol,))
        conexion.commit()
    finally:
        conexion.close()


def contar_usuarios_con_rol(nombre_rol):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS n FROM usuarios WHERE LOWER(rol) = LOWER(%s) AND activo = 1",
                (nombre_rol,),
            )
            return cursor.fetchone()["n"]
    finally:
        conexion.close()


# ---------------------------------------------------------------
# Enlace con la aplicación (creación de tablas)
# ---------------------------------------------------------------

def crear_tablas_configuracion():
    """Crea las tablas de configuración si no existen (no toca las demás)."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS etiquetas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(80) NOT NULL UNIQUE,
                    tipo VARCHAR(20) NOT NULL,
                    porcentaje DECIMAL(5,2) NOT NULL DEFAULT 0
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS parametros (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(80) NOT NULL UNIQUE,
                    etiqueta_id INT NOT NULL,
                    valor VARCHAR(255) NOT NULL,
                    descripcion TEXT,
                    FOREIGN KEY (etiqueta_id) REFERENCES etiquetas(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS roles (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(50) NOT NULL UNIQUE,
                    descripcion TEXT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS permisos (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(80) NOT NULL UNIQUE,
                    descripcion TEXT
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS rol_permiso (
                    rol_id INT NOT NULL,
                    permiso_id INT NOT NULL,
                    PRIMARY KEY (rol_id, permiso_id),
                    FOREIGN KEY (rol_id) REFERENCES roles(id) ON DELETE CASCADE,
                    FOREIGN KEY (permiso_id) REFERENCES permisos(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )

            cursor.execute("SELECT COUNT(*) AS n FROM roles")
            if cursor.fetchone()["n"] == 0:
                cursor.executemany(
                    "INSERT INTO roles (nombre, descripcion) VALUES (%s, %s)",
                    [
                        ("Administrador", "Acceso total al sistema"),
                        ("Contador", "Gestión contable y reportes"),
                        ("Auxiliar", "Apoyo contable y de inventario"),
                        ("Empleado", "Acceso básico de consulta"),
                    ],
                )

            cursor.execute("SELECT COUNT(*) AS n FROM permisos")
            if cursor.fetchone()["n"] == 0:
                cursor.executemany(
                    "INSERT INTO permisos (nombre, descripcion) VALUES (%s, %s)",
                    [
                        ("ver_inicio", "Ver página de inicio"),
                        ("ver_inventario", "Ver módulo de inventario"),
                        ("ver_nomina", "Ver módulo de nómina"),
                        ("ver_contabilidad", "Ver módulo de contabilidad"),
                        ("ver_configuracion", "Ver módulo de configuración"),
                        ("gestionar_usuarios", "Crear, editar y eliminar usuarios"),
                        ("gestionar_roles", "Crear, editar y eliminar roles"),
                        ("gestionar_etiquetas", "Crear, editar y eliminar etiquetas"),
                        ("gestionar_parametros", "Crear, editar y eliminar parámetros"),
                    ],
                )

            cursor.execute("SELECT COUNT(*) AS n FROM rol_permiso")
            if cursor.fetchone()["n"] == 0:
                # Se reparten los permisos demo entre los roles del sistema.
                reparto = {
                    "Administrador": None,  # todos
                    "Contador": ("ver_inicio", "ver_contabilidad", "ver_configuracion",
                                 "gestionar_etiquetas", "gestionar_parametros"),
                    "Auxiliar": ("ver_inicio", "ver_inventario", "ver_nomina"),
                    "Empleado": ("ver_inicio",),
                }
                for nombre_rol, nombres_permisos in reparto.items():
                    cursor.execute("SELECT id FROM roles WHERE nombre = %s", (nombre_rol,))
                    fila_rol = cursor.fetchone()
                    if fila_rol is None:
                        continue
                    if nombres_permisos is None:
                        cursor.execute("SELECT id FROM permisos")
                    else:
                        marcadores = ", ".join(["%s"] * len(nombres_permisos))
                        cursor.execute(
                            f"SELECT id FROM permisos WHERE nombre IN ({marcadores})",
                            nombres_permisos,
                        )
                    ids = [fila["id"] for fila in cursor.fetchall()]
                    cursor.executemany(
                        "INSERT INTO rol_permiso (rol_id, permiso_id) VALUES (%s, %s)",
                        [(fila_rol["id"], p) for p in ids],
                    )

        conexion.commit()
    finally:
        conexion.close()

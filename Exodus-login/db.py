import os
import pymysql
import pymysql.cursors
from flask import g
from werkzeug.security import generate_password_hash

from database.connection import obtener_conexion

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)


class Conexion:
    """Envuelve la conexión para usar db.execute(sql, params) como antes."""

    def __init__(self):
        self._con = obtener_conexion()

    def execute(self, sql, params=()):
        cur = self._con.cursor()
        cur.execute(sql, params)
        return cur

    def commit(self):
        self._con.commit()

    def close(self):
        self._con.close()


def get_db():
    if "db" not in g:
        g.db = Conexion()
    return g.db


def cerrar_db(_error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def iniciar_db():
    con = obtener_conexion()
    with con.cursor() as cur:
        cur.execute("""CREATE TABLE IF NOT EXISTS usuarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            usuario VARCHAR(50) NOT NULL UNIQUE,
            nombre VARCHAR(120) NOT NULL,
            clave_hash VARCHAR(255) NOT NULL,
            rol VARCHAR(20) NOT NULL,
            activo TINYINT(1) NOT NULL DEFAULT 1
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")

        cur.execute("""CREATE TABLE IF NOT EXISTS etiquetas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(80) NOT NULL UNIQUE,
            tipo VARCHAR(20) NOT NULL,
            porcentaje DECIMAL(5,2) NOT NULL DEFAULT 0
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")

        cur.execute("""CREATE TABLE IF NOT EXISTS parametros (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(80) NOT NULL UNIQUE,
            etiqueta_id INT NOT NULL,
            valor VARCHAR(255) NOT NULL,
            descripcion TEXT,
            FOREIGN KEY (etiqueta_id) REFERENCES etiquetas(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")

        cur.execute("""CREATE TABLE IF NOT EXISTS roles (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(50) NOT NULL UNIQUE,
            descripcion TEXT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")

        cur.execute("""CREATE TABLE IF NOT EXISTS permisos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(80) NOT NULL UNIQUE,
            descripcion TEXT
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")

        cur.execute("""CREATE TABLE IF NOT EXISTS rol_permiso (
            rol_id INT NOT NULL,
            permiso_id INT NOT NULL,
            PRIMARY KEY (rol_id, permiso_id),
            FOREIGN KEY (rol_id) REFERENCES roles(id) ON DELETE CASCADE,
            FOREIGN KEY (permiso_id) REFERENCES permisos(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4""")

        cur.execute("SELECT COUNT(*) AS n FROM usuarios")
        if cur.fetchone()["n"] == 0:
            demo = [
                ("admin", "Administrador del sistema", "admin123", "administrador"),
                ("contador", "Contador de prueba", "contador123", "contador"),
                ("rrhh", "Recursos Humanos de prueba", "rrhh123", "rrhh"),
            ]
            cur.executemany(
                "INSERT INTO usuarios (usuario, nombre, clave_hash, rol) VALUES (%s,%s,%s,%s)",
                [(u, n, generate_password_hash(c), r) for u, n, c, r in demo],
            )

        cur.execute("SELECT COUNT(*) AS n FROM roles")
        if cur.fetchone()["n"] == 0:
            roles_demo = [
                ("administrador", "Acceso total al sistema"),
                ("contador", "Gestión contable y reportes"),
                ("rrhh", "Gestión de nómina y empleados"),
            ]
            cur.executemany("INSERT INTO roles (nombre, descripcion) VALUES (%s,%s)", roles_demo)

        cur.execute("SELECT COUNT(*) AS n FROM permisos")
        if cur.fetchone()["n"] == 0:
            permisos_demo = [
                ("ver_inicio", "Ver página de inicio"),
                ("ver_inventario", "Ver módulo de inventario"),
                ("ver_nomina", "Ver módulo de nómina"),
                ("ver_contabilidad", "Ver módulo de contabilidad"),
                ("ver_configuracion", "Ver módulo de configuración"),
                ("gestionar_usuarios", "Crear, editar y eliminar usuarios"),
                ("gestionar_roles", "Crear, editar y eliminar roles"),
                ("gestionar_etiquetas", "Crear, editar y eliminar etiquetas"),
                ("gestionar_parametros", "Crear, editar y eliminar parámetros"),
            ]
            cur.executemany("INSERT INTO permisos (nombre, descripcion) VALUES (%s,%s)", permisos_demo)

        cur.execute("SELECT COUNT(*) AS n FROM rol_permiso")
        if cur.fetchone()["n"] == 0:
            cur.execute("SELECT id FROM roles WHERE nombre = 'administrador'")
            admin_id = cur.fetchone()["id"]
            cur.execute("SELECT id FROM permisos")
            todos = [r["id"] for r in cur.fetchall()]
            cur.executemany(
                "INSERT INTO rol_permiso (rol_id, permiso_id) VALUES (%s,%s)",
                [(admin_id, p) for p in todos],
            )

            cur.execute("SELECT id FROM roles WHERE nombre = 'contador'")
            contador_id = cur.fetchone()["id"]
            cur.execute("SELECT id FROM permisos WHERE nombre IN ('ver_inicio','ver_contabilidad','ver_configuracion','gestionar_etiquetas','gestionar_parametros')")
            contador_perms = [r["id"] for r in cur.fetchall()]
            cur.executemany(
                "INSERT INTO rol_permiso (rol_id, permiso_id) VALUES (%s,%s)",
                [(contador_id, p) for p in contador_perms],
            )

            cur.execute("SELECT id FROM roles WHERE nombre = 'rrhh'")
            rrhh_id = cur.fetchone()["id"]
            cur.execute("SELECT id FROM permisos WHERE nombre IN ('ver_inicio','ver_nomina')")
            rrhh_perms = [r["id"] for r in cur.fetchall()]
            cur.executemany(
                "INSERT INTO rol_permiso (rol_id, permiso_id) VALUES (%s,%s)",
                [(rrhh_id, p) for p in rrhh_perms],
            )

    con.commit()
    con.close()
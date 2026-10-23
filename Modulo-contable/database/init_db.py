from werkzeug.security import generate_password_hash

from database.connection import obtener_conexion

# Credenciales de demostración para los usuarios de prueba.
# La clave se guarda cifrada (hash), nunca en texto plano.
CREDENCIALES_DEMO = {
    "carlos": "carlos123",
    "ana": "ana123",
    "juan": "juan123",
    "admin": "admin123",
    "contador": "contador123",
    "auxiliar": "auxiliar123",
}


def _columnas(cursor, tabla):
    cursor.execute(
        """
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
        """,
        (tabla,),
    )
    return {fila["COLUMN_NAME"] for fila in cursor.fetchall()}


def iniciar_db():
    """Asegura que la tabla `usuarios` soporte inicio de sesión con usuario y contraseña."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            columnas = _columnas(cursor, "usuarios")

            if "usuario" not in columnas:
                cursor.execute(
                    "ALTER TABLE usuarios ADD COLUMN usuario VARCHAR(50) NULL UNIQUE AFTER id_usuario"
                )
            if "clave_hash" not in columnas:
                cursor.execute(
                    "ALTER TABLE usuarios ADD COLUMN clave_hash VARCHAR(255) NULL AFTER email"
                )
            if "activo" not in columnas:
                cursor.execute(
                    "ALTER TABLE usuarios ADD COLUMN activo TINYINT(1) NOT NULL DEFAULT 1"
                )

            cursor.execute("SELECT id_usuario, email, usuario, clave_hash FROM usuarios")
            for fila in cursor.fetchall():
                usuario = fila["usuario"] or (fila["email"] or "").split("@")[0]
                clave_demo = CREDENCIALES_DEMO.get(usuario)

                if not fila["clave_hash"] and clave_demo:
                    cursor.execute(
                        "UPDATE usuarios SET usuario = %s, clave_hash = %s, activo = 1 WHERE id_usuario = %s",
                        (usuario, generate_password_hash(clave_demo), fila["id_usuario"]),
                    )
                elif not fila["usuario"]:
                    cursor.execute(
                        "UPDATE usuarios SET usuario = %s WHERE id_usuario = %s",
                        (usuario, fila["id_usuario"]),
                    )

            # --- Migración: ampliar tabla gastos_deducibles (RF-11 Fase A) ---
            columnas_gastos = _columnas(cursor, "gastos_deducibles")
            if "categoria" not in columnas_gastos:
                cursor.execute(
                    "ALTER TABLE gastos_deducibles ADD COLUMN categoria VARCHAR(80) NULL AFTER descripcion"
                )
            if "tercero" not in columnas_gastos:
                cursor.execute(
                    "ALTER TABLE gastos_deducibles ADD COLUMN tercero VARCHAR(150) NULL AFTER categoria"
                )
            if "nit" not in columnas_gastos:
                cursor.execute(
                    "ALTER TABLE gastos_deducibles ADD COLUMN nit VARCHAR(30) NULL AFTER tercero"
                )
            if "numero_documento" not in columnas_gastos:
                cursor.execute(
                    "ALTER TABLE gastos_deducibles ADD COLUMN numero_documento VARCHAR(50) NULL AFTER nit"
                )
            if "estado_gasto" not in columnas_gastos:
                cursor.execute(
                    "ALTER TABLE gastos_deducibles ADD COLUMN estado_gasto ENUM('ACTIVO','ANULADO') NOT NULL DEFAULT 'ACTIVO' AFTER id_usuario"
                )

        conexion.commit()
    finally:
        conexion.close()

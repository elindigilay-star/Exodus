"""Punto de entrada único de EXODUS Contable.

Ejecuta TODA la aplicación (contabilidad, inventario, nómina y configuración)
desde un solo lugar y con una sola base de datos:

    python run.py
    python run.py --host 0.0.0.0 --port 5000 --debug
    python run.py --crear-admin admin MiClaveSegura "Administrador"

La configuración de la base de datos y de la clave secreta se lee de
variables de entorno (ver Modulo-contable/config.py y el README.md).
"""

import argparse
import os
import sys

import pymysql

RAIZ = os.path.dirname(os.path.abspath(__file__))
RUTA_APP = os.path.join(RAIZ, "Modulo-contable")

# `app.py` y `config.py` viven en Modulo-contable.
sys.path.insert(0, RUTA_APP)

from app import app  # noqa: E402  (crea la app y prepara la base de datos)
from config import DEBUG, HOST, PORT  # noqa: E402
from database.init_db import crear_admin  # noqa: E402


def _argumentos():
    """Lee los argumentos de la línea de comandos."""
    parser = argparse.ArgumentParser(
        description="EXODUS Contable - aplicación única del proyecto",
    )
    parser.add_argument(
        "--crear-admin", nargs=2, metavar=("USUARIO", "CLAVE"),
        help="crea un usuario Administrador y termina",
    )
    parser.add_argument(
        "--nombre", default="Administrador",
        help="nombre completo del usuario creado con --crear-admin",
    )
    parser.add_argument(
        "--email", default=None,
        help="correo del usuario creado con --crear-admin",
    )
    parser.add_argument("--host", default=HOST, help=f"host (por defecto {HOST})")
    parser.add_argument("--port", type=int, default=PORT,
                        help=f"puerto (por defecto {PORT})")
    parser.add_argument("--debug", action="store_true", default=DEBUG,
                        help="activa el depurador de Flask (solo desarrollo)")
    return parser.parse_args()


def main():
    """Arranca la aplicación o crea un administrador y termina."""
    args = _argumentos()

    if args.crear_admin:
        usuario, clave = args.crear_admin
        try:
            crear_admin(usuario, clave, args.nombre, args.email)
        except ValueError as error:
            print(f"ERROR: {error}")
            return 1
        except (pymysql.MySQLError, OSError) as error:
            print(f"ERROR: no se pudo usar la base de datos: {error}")
            return 1
        print(f"Usuario administrador {usuario!r} creado correctamente.")
        return 0

    print(f"EXODUS Contable en http://{args.host}:{args.port}  (Ctrl+C para salir)")
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


if __name__ == "__main__":
    sys.exit(main())

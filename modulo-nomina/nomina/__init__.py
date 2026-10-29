"""Módulo de nómina de EXODUS Contable (RF-6 a RF-9).

Todo el módulo vive en esta carpeta (`modulo-nomina/`) y se conecta a la
aplicación principal (`Modulo-contable/app.py`) con una sola llamada:

    from nomina import registrar_nomina

    registrar_nomina(app)

`registrar_nomina(app)` registra las rutas en /api/nomina, deja disponible la
vista /api/nomina/modulo y se asegura de que las tablas (empleados,
deducciones, aportes, nomina, novedades) existan.

El módulo comparte la base de datos MySQL `sistema_contable` con el resto de
Modulo-contable (por eso `modelo.py` usa `database.connection.obtener_conexion`)
y también comparte la sesión de usuarios (por eso `rutas.py` usa
`routes.auth.requerir_roles`).

Esta es la única versión del módulo: se ejecuta dentro de la aplicación
principal y comparte su base de datos y su sesión de usuarios.
"""

from .rutas import registrar_nomina

__all__ = ['registrar_nomina']

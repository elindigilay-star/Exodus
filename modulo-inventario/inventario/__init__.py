"""Módulo de inventario de EXODUS Contable (RF-01 a RF-05).

Todo el módulo vive en esta carpeta (`modulo-inventario/`) y se conecta a la
aplicación principal (`Modulo-contable/app.py`) con una sola llamada:

    from inventario import registrar_inventario

    registrar_inventario(app)

`registrar_inventario(app)` registra las rutas en /api/inventario, deja
disponible la vista /api/inventario/modulo y se asegura de que las tablas
(productos, movimientos_inventario) existan.

El módulo comparte la base de datos MySQL `sistema_contable` con el resto de
Modulo-contable (por eso `stock.py` y `resumen.py` usan
`database.connection.obtener_conexion`), y también comparte la sesión de
usuarios (por eso `rutas.py` usa `routes.auth.requerir_roles`).
"""

from .rutas import registrar_inventario

__all__ = ['registrar_inventario']

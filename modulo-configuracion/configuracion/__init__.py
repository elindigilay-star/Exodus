"""Módulo de configuración de EXODUS Contable.

Todo el módulo vive en esta carpeta (`modulo-configuracion/`) y se conecta a
la aplicación principal (`Modulo-contable/app.py`) con una sola llamada:

    from configuracion import registrar_configuracion

    registrar_configuracion(app)

`registrar_configuracion(app)` registra las rutas bajo /configuracion
(etiquetas, parámetros, roles y permisos, usuarios) y se asegura de que las
tablas del catálogo (etiquetas, parametros, roles, permisos, rol_permiso)
existan en la base `sistema_contable`.

Las páginas de etiquetas, parámetros, roles/permisos y usuarios comparten la
misma base de datos y la misma sesión que el resto de la aplicación. El
mantenimiento de usuarios reutiliza `models.usuario` de Modulo-contable,
porque es la misma tabla `usuarios` del inicio de sesión.
"""

from .rutas import registrar_configuracion

__all__ = ['registrar_configuracion']

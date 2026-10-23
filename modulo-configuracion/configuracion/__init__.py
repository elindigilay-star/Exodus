"""Módulo de configuración de EXODUS Contable.

Todo el módulo vive en esta carpeta (`modulo-configuracion/`) y se conecta a
la aplicación principal (`Modulo-contable/app.py`) con una sola llamada:

    from configuracion import registrar_configuracion

    registrar_configuracion(app)

`registrar_configuracion(app)` registra las rutas bajo /configuracion
(parámetros, roles y permisos, usuarios) y se asegura de que las
tablas del catálogo (parametros, roles, permisos, rol_permiso)
existan en la base `sistema_contable`.

Las páginas de parámetros y roles/permisos se trajeron de
`Exodus-login` (ahí vivían con su propia base `exodus_contable`); en esta
versión usan la misma base y la misma sesión de usuarios que el resto de la
aplicación. El mantenimiento de usuarios reutiliza `models.usuario` de
Modulo-contable, porque es la misma tabla `usuarios` del inicio de sesión.

Las etiquetas se movieron al módulo de inventario (`modulo-inventario/inventario/etiquetas.py`).
"""

from .rutas import registrar_configuracion

__all__ = ['registrar_configuracion']

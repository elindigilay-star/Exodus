"""Rutas del módulo de configuración.

Un solo blueprint (`configuracion`) agrupa las cuatro páginas:
  - /configuracion/etiquetas            (Administrador, Contador)
  - /configuracion/parametros           (Administrador, Contador)
  - /configuracion/roles                (Administrador)
  - /configuracion/usuarios             (Administrador)

Cada página vive en su propio archivo (etiquetas.py, parametros.py, roles.py,
usuarios.py) y añade sus rutas a este mismo blueprint.
"""

from flask import Blueprint

configuracion_bp = Blueprint(
    'configuracion', __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/configuracion/static',
)

# Importar los archivos de rutas registra sus vistas en el blueprint.
# Debe ir al final para que `configuracion_bp` ya exista.
from . import usuarios, etiquetas, parametros, roles  # noqa: E402,F401


def registrar_configuracion(app):
    """Registra el blueprint y prepara las tablas. Se llama una vez desde app.py.

    Se monta sin prefijo adicional:
      - etiquetas:  /configuracion/etiquetas
      - parámetros: /configuracion/parametros
      - roles:      /configuracion/roles
      - usuarios:   /configuracion/usuarios
      - static:     /configuracion/static/css/configuracion.css
    """
    app.register_blueprint(configuracion_bp)
    try:
        from . import modelo
        modelo.crear_tablas_configuracion()
    except Exception as error:  # La app arranca aunque la base de datos esté apagada
        print(f"AVISO: no se pudieron preparar las tablas de configuración: {error}")

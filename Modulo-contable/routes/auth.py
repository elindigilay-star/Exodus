"""Inicio de sesión, cierre de sesión y decoradores de permisos."""

from functools import wraps

from flask import (Blueprint, abort, flash, jsonify, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash

from models.usuario import (limpiar_intentos, obtener_usuario_por_id,
                            obtener_usuario_por_usuario, registrar_intento_fallido,
                            segundos_bloqueado)

auth_bp = Blueprint('auth', __name__)

COOKIE_USUARIO = "exodus_usuario"
MAX_INTENTOS = 5
BLOQUEO_SEGUNDOS = 300

# El rol puede venir en la base en minúsculas (versiones viejas del script
# SQL) o con mayúscula inicial (versión actual). Aquí se unifica siempre a la
# forma con mayúscula inicial para que el resto del sistema compare sin líos.
ROLES_CANONICOS = {
    'administrador': 'Administrador',
    'contador': 'Contador',
    'auxiliar': 'Auxiliar',
    'empleado': 'Empleado',
    'recursos humanos': 'Recursos Humanos',
    'rrhh': 'Recursos Humanos',
}


def rol_canonico(valor):
    """Devuelve el rol en su forma estándar ('Administrador', 'Contador', ...)."""
    if not valor:
        return valor
    limpio = str(valor).strip()
    return ROLES_CANONICOS.get(limpio.lower(), limpio)


def _ip_cliente():
    return request.remote_addr or '0.0.0.0'


def _minutos_bloqueado(usuario):
    """Minutos restantes de bloqueo (redondeados hacia arriba)."""
    segundos = segundos_bloqueado(usuario.lower(), _ip_cliente())
    return (segundos + 59) // 60 if segundos else 0


def _registrar_fallo(usuario):
    registrar_intento_fallido(usuario.lower(), _ip_cliente(), MAX_INTENTOS, BLOQUEO_SEGUNDOS)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Inicia sesión con usuario y contraseña."""
    if session.get('usuario_id'):
        return redirect(url_for('inicio'))

    recordado = request.cookies.get(COOKIE_USUARIO, "")
    valores = {"usuario_valor": recordado, "recordar": bool(recordado)}

    if request.method == 'POST':
        usuario_valor = (request.form.get('usuario') or '').strip()
        clave = request.form.get('clave') or ''
        recordar = request.form.get('recordar') == 'on'
        valores = {"usuario_valor": usuario_valor, "recordar": recordar}

        if not usuario_valor or not clave:
            flash("Escribe tu usuario y tu contraseña.", "error")
            return render_template('login.html', **valores), 400

        minutos = _minutos_bloqueado(usuario_valor)
        if minutos:
            flash(
                f"Demasiados intentos fallidos. "
                f"Espera {minutos} min e inténtalo de nuevo.",
                "error",
            )
            return render_template('login.html', **valores), 429

        fila = obtener_usuario_por_usuario(usuario_valor)

        if (fila is None or not fila.get('clave_hash')
                or not check_password_hash(fila['clave_hash'], clave)):
            _registrar_fallo(usuario_valor)
            flash("Usuario o contraseña incorrectos.", "error")
            return render_template('login.html', **valores), 401

        if not fila['activo']:
            flash("Tu usuario está inactivo. Pide al administrador que lo active.", "error")
            return render_template('login.html', **valores), 403

        limpiar_intentos(usuario_valor.lower(), _ip_cliente())
        session.clear()
        session['usuario_id'] = fila['id_usuario']
        session['usuario_nombre'] = fila['nombre']
        session['usuario_rol'] = rol_canonico(fila['rol'])

        respuesta = redirect(url_for('inicio'))
        if recordar:
            # Solo se guarda el nombre de usuario, nunca la contraseña.
            respuesta.set_cookie(COOKIE_USUARIO, fila['usuario'],
                                 max_age=60 * 60 * 24 * 30,
                                 httponly=True, samesite="Lax")
        else:
            respuesta.delete_cookie(COOKIE_USUARIO)
        return respuesta

    return render_template('login.html', **valores)


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Cierra la sesión activa."""
    session.clear()
    return redirect(url_for('auth.login'))


def login_requerido(f):
    """Decorador para exigir una sesión activa (cualquier rol)."""
    @wraps(f)
    def funcion_decorada(*args, **kwargs):
        if not session.get('usuario_id'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return funcion_decorada


def requerir_roles(*roles_permitidos):
    """Decorador para restringir el acceso a rutas según el rol del usuario."""
    def decorador(f):
        @wraps(f)
        def funcion_decorada(*args, **kwargs):
            id_usuario = session.get('usuario_id')

            if not id_usuario:
                return redirect(url_for('auth.login'))

            usuario = obtener_usuario_por_id(id_usuario)

            if not usuario or not usuario.get('activo'):
                session.clear()
                return redirect(url_for('auth.login'))

            if rol_canonico(usuario['rol']) not in roles_permitidos:
                abort(403)

            return f(*args, **kwargs)
        return funcion_decorada
    return decorador


# ---------------------------------------------------------------
# Decoradores para la API (responden JSON, no redirecciones)
# ---------------------------------------------------------------

def api_login_requerido(f):
    """Exige sesión en una ruta /api/ y responde 401 en JSON."""
    @wraps(f)
    def funcion_decorada(*args, **kwargs):
        if not session.get('usuario_id'):
            return jsonify({'error': 'Tu sesión expiró. Inicia sesión de nuevo.'}), 401
        return f(*args, **kwargs)
    return funcion_decorada


def api_requerir_roles(*roles_permitidos):
    """Exige sesión y rol en una ruta /api/ y responde 401/403 en JSON."""
    def decorador(f):
        @wraps(f)
        def funcion_decorada(*args, **kwargs):
            id_usuario = session.get('usuario_id')
            if not id_usuario:
                return jsonify({'error': 'Tu sesión expiró. Inicia sesión de nuevo.'}), 401

            usuario = obtener_usuario_por_id(id_usuario)
            if not usuario:
                return jsonify({'error': 'Tu usuario ya no existe.'}), 401
            if not usuario.get('activo'):
                return jsonify({'error': 'Tu usuario está inactivo.'}), 401

            if rol_canonico(usuario['rol']) not in roles_permitidos:
                return jsonify({'error': 'Tu rol no tiene permiso para esta operación.'}), 403
            return f(*args, **kwargs)
        return funcion_decorada
    return decorador

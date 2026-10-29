"""Página de configuración: Roles y permisos (solo Administrador)."""

import pymysql
from flask import abort, flash, redirect, render_template, request, url_for

from routes.auth import requerir_roles

from . import modelo
from .rutas import configuracion_bp

ROLES = ('Administrador',)


def _leer_formulario():
    nombre = request.form.get('nombre', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    permisos = request.form.getlist('permisos')
    if not nombre:
        return None, 'Escribe el nombre del rol.'
    return (nombre, descripcion, [int(p) for p in permisos]), None


def _render(editar=None):
    return render_template(
        'configuracion/roles.html',
        lista=modelo.listar_roles_con_permisos(),
        todos_permisos=modelo.listar_permisos(),
        editar=editar,
    )


@configuracion_bp.route('/configuracion/roles', methods=['GET', 'POST'])
@requerir_roles(*ROLES)
def roles_index():
    if request.method == 'POST':
        datos, error = _leer_formulario()
        if error:
            flash(error, 'error')
        else:
            try:
                modelo.crear_rol(*datos)
                flash('Rol creado.', 'ok')
                return redirect(url_for('configuracion.roles_index'))
            except pymysql.err.IntegrityError:
                flash('Ya existe un rol con ese nombre.', 'error')
    return _render()


@configuracion_bp.route('/configuracion/roles/<int:id_rol>/editar', methods=['GET', 'POST'])
@requerir_roles(*ROLES)
def roles_editar(id_rol):
    fila = modelo.obtener_rol(id_rol)
    if fila is None:
        abort(404)
    if request.method == 'POST':
        datos, error = _leer_formulario()
        if error:
            flash(error, 'error')
        else:
            try:
                modelo.actualizar_rol(id_rol, *datos)
                flash('Rol actualizado.', 'ok')
                return redirect(url_for('configuracion.roles_index'))
            except pymysql.err.IntegrityError:
                flash('Ya existe un rol con ese nombre.', 'error')
    editar_data = dict(fila)
    editar_data['permisos_ids'] = [p['id'] for p in modelo.listar_permisos_de_rol(id_rol)]
    return _render(editar=editar_data)


@configuracion_bp.route('/configuracion/roles/<int:id_rol>/eliminar', methods=['POST'])
@requerir_roles(*ROLES)
def roles_eliminar(id_rol):
    fila = modelo.obtener_rol(id_rol)
    if fila is None:
        abort(404)
    en_uso = modelo.contar_usuarios_con_rol(fila['nombre'])
    if en_uso > 0:
        flash(f'No se puede eliminar: hay {en_uso} usuario(s) activo(s) con este rol.', 'error')
    else:
        modelo.eliminar_rol(id_rol)
        flash('Rol eliminado.', 'ok')
    return redirect(url_for('configuracion.roles_index'))

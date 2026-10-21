"""Página de configuración: Parámetros (valores legales o de negocio)."""

import pymysql
from flask import abort, flash, redirect, render_template, request, url_for

from routes.auth import requerir_roles

from . import modelo
from .rutas import configuracion_bp

ROLES = ('Administrador', 'Contador')


def _leer_formulario():
    nombre = request.form.get('nombre', '').strip()
    etiqueta_id = request.form.get('etiqueta_id', '')
    valor = request.form.get('valor', '').strip()
    descripcion = request.form.get('descripcion', '').strip()
    if not nombre:
        return None, 'Escribe el nombre del parámetro.'
    if not etiqueta_id:
        return None, 'Selecciona una etiqueta.'
    try:
        etiqueta_id = int(etiqueta_id)
    except ValueError:
        return None, 'Etiqueta no válida.'
    if not valor:
        return None, 'Escribe el valor del parámetro.'
    return (nombre, etiqueta_id, valor, descripcion), None


def _render(editar=None):
    return render_template(
        'configuracion/parametros.html',
        lista=modelo.listar_parametros(),
        etiquetas=modelo.listar_etiquetas(),
        editar=editar,
    )


@configuracion_bp.route('/configuracion/parametros', methods=['GET', 'POST'])
@requerir_roles(*ROLES)
def parametros_index():
    if request.method == 'POST':
        datos, error = _leer_formulario()
        if error:
            flash(error, 'error')
        else:
            try:
                modelo.crear_parametro(*datos)
                flash('Parámetro creado.', 'ok')
                return redirect(url_for('configuracion.parametros_index'))
            except pymysql.err.IntegrityError:
                flash('Ya existe un parámetro con ese nombre.', 'error')
    return _render()


@configuracion_bp.route('/configuracion/parametros/<int:id>/editar', methods=['GET', 'POST'])
@requerir_roles(*ROLES)
def parametros_editar(id):
    fila = modelo.obtener_parametro(id)
    if fila is None:
        abort(404)
    if request.method == 'POST':
        datos, error = _leer_formulario()
        if error:
            flash(error, 'error')
        else:
            try:
                modelo.actualizar_parametro(id, *datos)
                flash('Parámetro actualizado.', 'ok')
                return redirect(url_for('configuracion.parametros_index'))
            except pymysql.err.IntegrityError:
                flash('Ya existe un parámetro con ese nombre.', 'error')
    return _render(editar=fila)


@configuracion_bp.route('/configuracion/parametros/<int:id>/eliminar', methods=['POST'])
@requerir_roles(*ROLES)
def parametros_eliminar(id):
    modelo.eliminar_parametro(id)
    flash('Parámetro eliminado.', 'ok')
    return redirect(url_for('configuracion.parametros_index'))

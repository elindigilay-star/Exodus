import pymysql
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from db import get_db
from seguridad import rol_requerido

bp = Blueprint("parametros", __name__, url_prefix="/configuracion/parametros")
ROLES = ("administrador", "contador")


def _listar():
    return get_db().execute(
        """SELECT p.*, e.nombre AS etiqueta_nombre
           FROM parametros p
           JOIN etiquetas e ON e.id = p.etiqueta_id
           ORDER BY p.nombre"""
    ).fetchall()


def _etiquetas():
    return get_db().execute("SELECT * FROM etiquetas ORDER BY nombre").fetchall()


def _leer_formulario():
    nombre = request.form.get("nombre", "").strip()
    etiqueta_id = request.form.get("etiqueta_id", "")
    valor = request.form.get("valor", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    if not nombre:
        return None, "Escribe el nombre del parámetro."
    if not etiqueta_id:
        return None, "Selecciona una etiqueta."
    try:
        etiqueta_id = int(etiqueta_id)
    except ValueError:
        return None, "Etiqueta no válida."
    if not valor:
        return None, "Escribe el valor del parámetro."
    return (nombre, etiqueta_id, valor, descripcion), None


@bp.route("/", methods=["GET", "POST"])
@rol_requerido(*ROLES)
def index():
    if request.method == "POST":
        datos, error = _leer_formulario()
        if error:
            flash(error, "error")
        else:
            try:
                db = get_db()
                db.execute(
                    "INSERT INTO parametros (nombre, etiqueta_id, valor, descripcion) VALUES (%s,%s,%s,%s)",
                    datos,
                )
                db.commit()
                flash("Parámetro creado.", "ok")
                return redirect(url_for("parametros.index"))
            except pymysql.err.IntegrityError:
                flash("Ya existe un parámetro con ese nombre.", "error")
    return render_template(
        "configuracion/parametros.html",
        lista=_listar(),
        etiquetas=_etiquetas(),
        editar=None,
    )


@bp.route("/<int:id>/editar", methods=["GET", "POST"])
@rol_requerido(*ROLES)
def editar(id):
    db = get_db()
    fila = db.execute("SELECT * FROM parametros WHERE id = %s", (id,)).fetchone()
    if fila is None:
        abort(404)
    if request.method == "POST":
        datos, error = _leer_formulario()
        if error:
            flash(error, "error")
        else:
            try:
                db.execute(
                    "UPDATE parametros SET nombre=%s, etiqueta_id=%s, valor=%s, descripcion=%s WHERE id=%s",
                    (*datos, id),
                )
                db.commit()
                flash("Parámetro actualizado.", "ok")
                return redirect(url_for("parametros.index"))
            except pymysql.err.IntegrityError:
                flash("Ya existe un parámetro con ese nombre.", "error")
    return render_template(
        "configuracion/parametros.html",
        lista=_listar(),
        etiquetas=_etiquetas(),
        editar=fila,
    )


@bp.route("/<int:id>/eliminar", methods=["POST"])
@rol_requerido(*ROLES)
def eliminar(id):
    db = get_db()
    db.execute("DELETE FROM parametros WHERE id = %s", (id,))
    db.commit()
    flash("Parámetro eliminado.", "ok")
    return redirect(url_for("parametros.index"))

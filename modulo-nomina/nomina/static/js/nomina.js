/**
 * nomina.js - Módulo de Nómina dentro de Exodus Contable (Flask).
 * Consume los endpoints JSON bajo /api/nomina: empleados, periodos,
 * novedades del motor (horas extras), parámetros y solicitudes.
 */

const API = '/api/nomina';

function formatoMoneda(valor) {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(Number(valor || 0));
}

function escapar(valor) {
  return String(valor ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

function mostrarMensaje(id, texto, tipo) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = texto;
  el.className = `msg show ${tipo}`;
  setTimeout(() => el.classList.remove('show'), 5000);
}

async function llamarApi(endpoint, opciones = {}) {
  const respuesta = await fetch(`${API}/${endpoint}`, opciones);
  const datos = await respuesta.json().catch(() => ({}));
  if (!respuesta.ok) {
    throw new Error(datos.error || datos.mensaje || 'Ocurrió un error inesperado.');
  }
  return datos;
}

function post(endpoint, cuerpo) {
  return llamarApi(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cuerpo),
  });
}

function datosDe(body) {
  return body && body.data !== undefined ? body.data : body;
}

// ---------------------------------------------------------------
// Navegación entre vistas
// ---------------------------------------------------------------
document.querySelectorAll('.nomina .tab').forEach((boton) => {
  boton.addEventListener('click', () => {
    document.querySelectorAll('.nomina .tab').forEach((b) => b.classList.remove('active'));
    document.querySelectorAll('.nomina .view').forEach((v) => v.classList.remove('active'));

    boton.classList.add('active');
    document.getElementById(`view-${boton.dataset.view}`).classList.add('active');

    if (boton.dataset.view === 'historial') cargarPeriodos();
    if (boton.dataset.view === 'parametros') cargarParametros();
    if (boton.dataset.view === 'extras') cargarExtras();
  });
});

// ---------------------------------------------------------------
// RF-6 / RF-7: Empleados
// ---------------------------------------------------------------
async function cargarEmpleados() {
  const tabla = document.getElementById('tabla-empleados');
  try {
    const empleados = datosDe(await llamarApi('empleados')) || [];

    if (empleados.length === 0) {
      tabla.innerHTML = '<tr class="empty-row"><td colspan="9">Aún no hay empleados registrados.</td></tr>';
    } else {
      tabla.innerHTML = empleados.map((emp) => `
        <tr>
          <td>${escapar(emp.nombres)} ${escapar(emp.apellidos)}</td>
          <td>${escapar(emp.documento)}</td>
          <td>${escapar(emp.cargo || '—')}</td>
          <td class="num">${formatoMoneda(emp.salario_base)}</td>
          <td>${escapar(emp.tipo_contrato || '—')}</td>
          <td>${escapar(emp.riesgo_arl || 1)}</td>
          <td>${escapar(emp.fecha_ingreso)}</td>
          <td><span class="badge ${String(emp.estado || '').toLowerCase()}">${escapar(emp.estado)}</span></td>
          <td>${emp.estado === 'ACTIVO'
            ? `<button class="link-danger" data-eliminar="${emp.id_empleado}">Retirar</button>`
            : ''}</td>
        </tr>
      `).join('');
    }

    llenarSelectEmpleados(empleados.filter((e) => e.estado === 'ACTIVO'));
  } catch (err) {
    tabla.innerHTML = `<tr class="empty-row"><td colspan="9">${escapar(err.message)}</td></tr>`;
  }
}

function llenarSelectEmpleados(activos) {
  const opciones = activos
    .map((e) => `<option value="${e.id_empleado}">${escapar(e.nombres)} ${escapar(e.apellidos)} — ${escapar(e.documento)}</option>`)
    .join('');

  ['nom-empleado', 'ext-empleado', 'nov-empleado'].forEach((id) => {
    const select = document.getElementById(id);
    if (select) select.innerHTML = opciones || '<option value="">No hay empleados activos</option>';
  });
}

document.getElementById('form-empleado').addEventListener('submit', async (evento) => {
  evento.preventDefault();
  const form = evento.target;
  const datos = Object.fromEntries(new FormData(form).entries());
  datos.salario_integral = form.querySelector('[name="salario_integral"]').checked ? 1 : 0;
  datos.exonerado_salud = form.querySelector('[name="exonerado_salud"]').checked ? 1 : 0;
  datos.exonerado_parafiscales = form.querySelector('[name="exonerado_parafiscales"]').checked ? 1 : 0;

  try {
    const resultado = await post('empleados', datos);
    mostrarMensaje('msg-empleado', resultado.mensaje, 'ok');
    form.reset();
    cargarEmpleados();
  } catch (err) {
    mostrarMensaje('msg-empleado', err.message, 'error');
  }
});

document.getElementById('tabla-empleados').addEventListener('click', async (evento) => {
  const id = evento.target.dataset.eliminar;
  if (!id) return;

  if (!confirm('¿Retirar este empleado? Quedará marcado como inactivo.')) return;

  try {
    await post('empleados/eliminar', { id_empleado: id });
    cargarEmpleados();
  } catch (err) {
    alert(err.message);
  }
});

// ---------------------------------------------------------------
// RF-8: Liquidar periodo
// ---------------------------------------------------------------
document.getElementById('form-periodo').addEventListener('submit', async (evento) => {
  evento.preventDefault();
  const form = evento.target;
  const datos = Object.fromEntries(new FormData(form).entries());

  try {
    const resultado = datosDe(await post('periodos/liquidar', datos)) || {};
    mostrarMensaje('msg-periodo', 'Nómina liquidada correctamente.', 'ok');

    document.getElementById('per-rep-empleados').textContent = resultado.empleados ?? '—';
    document.getElementById('per-rep-devengado').textContent = formatoMoneda(resultado.total_devengado);
    document.getElementById('per-rep-deducciones').textContent = formatoMoneda(resultado.total_deducciones);
    document.getElementById('per-rep-aportes').textContent = formatoMoneda(resultado.total_aportes);
    document.getElementById('per-rep-provisiones').textContent = formatoMoneda(resultado.total_provisiones);
    document.getElementById('per-rep-neto').textContent = formatoMoneda(resultado.total_neto);
    document.getElementById('per-rep-costo').textContent = formatoMoneda(
      Number(resultado.total_devengado || 0) + Number(resultado.total_aportes || 0) + Number(resultado.total_provisiones || 0)
    );
    document.getElementById('reporte-periodo').classList.add('show');

    cargarPeriodos();
  } catch (err) {
    mostrarMensaje('msg-periodo', err.message, 'error');
  }
});

async function cargarPeriodos() {
  const tabla = document.getElementById('tabla-periodos');
  if (!tabla) return;
  try {
    const periodos = datosDe(await llamarApi('periodos')) || [];
    if (!periodos.length) {
      tabla.innerHTML = '<tr class="empty-row"><td colspan="8">Aún no se ha liquidado ningún periodo.</td></tr>';
      return;
    }
    tabla.innerHTML = periodos.map((p) => `
      <tr>
        <td>${escapar(p.nombre)}</td>
        <td>${escapar(p.tipo)}</td>
        <td>${escapar(p.fecha_inicio)}</td>
        <td>${escapar(p.fecha_fin)}</td>
        <td class="num">${formatoMoneda(p.total_devengado)}</td>
        <td class="num">${formatoMoneda(p.total_neto)}</td>
        <td><span class="badge ${String(p.estado || '').toLowerCase()}">${escapar(p.estado)}</span></td>
        <td>
          <button class="link-approve" data-ver-periodo="${p.id_periodo}">Ver</button>
          ${p.estado === 'CALCULADO'
            ? `<button class="link-approve" data-contabilizar="${p.id_periodo}">Contabilizar</button>`
            : ''}
        </td>
      </tr>
    `).join('');
  } catch (err) {
    tabla.innerHTML = `<tr class="empty-row"><td colspan="8">${escapar(err.message)}</td></tr>`;
  }
}

document.getElementById('tabla-periodos').addEventListener('click', async (evento) => {
  const idVer = evento.target.dataset.verPeriodo;
  const idCont = evento.target.dataset.contabilizar;

  if (idVer) {
    verPeriodo(idVer);
  }
  if (idCont) {
    if (!confirm('¿Generar el comprobante contable de este periodo? El periodo quedará bloqueado.')) return;
    try {
      await post(`periodos/${idCont}/contabilizar`, {});
      cargarPeriodos();
    } catch (err) {
      alert(err.message);
    }
  }
});

async function verPeriodo(idPeriodo) {
  const panel = document.getElementById('panel-detalle-periodo');
  const contenedor = document.getElementById('detalle-periodo');
  panel.style.display = 'block';
  contenedor.innerHTML = 'Cargando…';

  try {
    const periodo = datosDe(await llamarApi(`periodos/${idPeriodo}`));
    document.getElementById('detalle-titulo').textContent =
      `${periodo.nombre} · ${periodo.fecha_inicio} a ${periodo.fecha_fin}`;

    const filas = (periodo.detalles || []).map((d) => `
      <tr>
        <td>${escapar(d.empleado)}</td>
        <td>${escapar(d.documento)}</td>
        <td class="num">${formatoMoneda(d.total_devengado)}</td>
        <td class="num">${formatoMoneda(d.ibc)}</td>
        <td class="num">${formatoMoneda(d.total_deducciones)}</td>
        <td class="num">${formatoMoneda(d.neto_pagar)}</td>
        <td>
          <a class="link-approve" target="_blank"
             href="${API}/periodos/${periodo.id_periodo}/colilla/${d.id_empleado}">Colilla</a>
        </td>
      </tr>
    `).join('');

    contenedor.innerHTML = `
      <div class="report-card show" style="margin-bottom:16px;">
        <div class="report-line"><span>Total devengado</span><span>${formatoMoneda(periodo.total_devengado)}</span></div>
        <div class="report-line"><span>Deducciones</span><span>${formatoMoneda(periodo.total_deducciones)}</span></div>
        <div class="report-line"><span>Aportes patronales</span><span>${formatoMoneda(periodo.total_aportes)}</span></div>
        <div class="report-line"><span>Provisiones</span><span>${formatoMoneda(periodo.total_provisiones)}</span></div>
        <div class="report-line total"><span>Neto a pagar</span><span>${formatoMoneda(periodo.total_neto)}</span></div>
      </div>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Empleado</th>
              <th>Documento</th>
              <th class="num">Devengado</th>
              <th class="num">IBC</th>
              <th class="num">Deducciones</th>
              <th class="num">Neto</th>
              <th></th>
            </tr>
          </thead>
          <tbody>${filas || '<tr class="empty-row"><td colspan="7">Sin empleados.</td></tr>'}</tbody>
        </table>
      </div>
    `;
    panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (err) {
    contenedor.innerHTML = `<p style="color:#B42318;">${escapar(err.message)}</p>`;
  }
}

// ---------------------------------------------------------------
// Horas extras y deducciones (novedades del motor)
// ---------------------------------------------------------------
let conceptosNomina = [];

async function cargarConceptos() {
  try {
    conceptosNomina = datosDe(await llamarApi('conceptos')) || [];
    const select = document.getElementById('ext-concepto');
    const automaticos = new Set([
      'SALARIO', 'AUX_TRANSPORTE', 'SALUD_EMPLEADO', 'PENSION_EMPLEADO', 'FSP',
    ]);
    const disponibles = conceptosNomina.filter(
      (c) => ['DEVENGADO', 'DEDUCCION'].includes(c.tipo) && !automaticos.has(c.codigo)
    );
    select.innerHTML = disponibles.map((c) => `
      <option value="${escapar(c.codigo)}" data-tipo="${escapar(c.tipo)}">${escapar(c.codigo)} — ${escapar(c.nombre)}</option>
    `).join('');
  } catch (err) {
    console.warn('No se pudieron cargar los conceptos de nómina:', err);
  }
}

document.getElementById('form-extra').addEventListener('submit', async (evento) => {
  evento.preventDefault();
  const form = evento.target;
  const datos = Object.fromEntries(new FormData(form).entries());

  try {
    const resultado = await post('novedades-nomina', datos);
    mostrarMensaje('msg-extra', resultado.mensaje, 'ok');
    form.reset();
    document.getElementById('ext-fecha').value = new Date().toISOString().slice(0, 10);
    cargarExtras();
  } catch (err) {
    mostrarMensaje('msg-extra', err.message, 'error');
  }
});

async function cargarExtras() {
  const tabla = document.getElementById('tabla-extras');
  if (!tabla) return;
  try {
    const novedades = datosDe(await llamarApi('novedades-nomina')) || [];
    if (!novedades.length) {
      tabla.innerHTML = '<tr class="empty-row"><td colspan="7">No hay novedades activas.</td></tr>';
      return;
    }
    tabla.innerHTML = novedades.map((n) => `
      <tr>
        <td>${escapar(n.nombres)} ${escapar(n.apellidos)}</td>
        <td>${escapar(n.concepto)}</td>
        <td>${escapar(n.fecha)}</td>
        <td class="num">${Number(n.cantidad || 0)}</td>
        <td class="num">${formatoMoneda(n.valor_total ?? n.valor_unitario)}</td>
        <td>${escapar(n.descripcion || '—')}</td>
        <td><button class="link-danger" data-anular-extra="${n.id_novedad_nomina}">Anular</button></td>
      </tr>
    `).join('');
  } catch (err) {
    tabla.innerHTML = `<tr class="empty-row"><td colspan="7">${escapar(err.message)}</td></tr>`;
  }
}

document.getElementById('tabla-extras').addEventListener('click', async (evento) => {
  const id = evento.target.dataset.anularExtra;
  if (!id) return;
  if (!confirm('¿Anular esta novedad?')) return;
  try {
    await post('novedades-nomina/anular', { id_novedad_nomina: id });
    cargarExtras();
  } catch (err) {
    alert(err.message);
  }
});

// ---------------------------------------------------------------
// Parámetros legales
// ---------------------------------------------------------------
async function cargarParametros() {
  const tabla = document.getElementById('tabla-parametros');
  if (!tabla) return;
  try {
    const cuerpo = await llamarApi('parametros');
    const parametros = cuerpo.data || [];
    if (!parametros.length) {
      tabla.innerHTML = '<tr class="empty-row"><td colspan="4">No hay parámetros configurados.</td></tr>';
      return;
    }
    tabla.innerHTML = parametros.map((p) => `
      <tr>
        <td>${escapar(p.clave)}</td>
        <td>${escapar(p.descripcion || '')}</td>
        <td class="num">
          <input type="number" step="0.0001" data-parametro="${escapar(p.clave)}"
                 value="${Number(p.valor || 0)}" style="text-align:right;max-width:150px;">
        </td>
        <td>${escapar(p.unidad)}</td>
      </tr>
    `).join('');
  } catch (err) {
    tabla.innerHTML = `<tr class="empty-row"><td colspan="4">${escapar(err.message)}</td></tr>`;
  }
}

document.getElementById('btn-guardar-parametros').addEventListener('click', async () => {
  const parametros = [];
  document.querySelectorAll('[data-parametro]').forEach((input) => {
    parametros.push({ clave: input.dataset.parametro, valor: input.value });
  });
  try {
    const resultado = await post('parametros', { parametros });
    mostrarMensaje('msg-parametros', resultado.mensaje, 'ok');
  } catch (err) {
    mostrarMensaje('msg-parametros', err.message, 'error');
  }
});

// ---------------------------------------------------------------
// RF-9: Ausencias, vacaciones y permisos (solicitudes)
// ---------------------------------------------------------------
async function cargarNovedades() {
  const tabla = document.getElementById('tabla-novedades');
  if (!tabla) return;
  try {
    const novedades = datosDe(await llamarApi('novedades')) || [];

    tabla.innerHTML = novedades.length === 0
      ? '<tr class="empty-row"><td colspan="6">Aún no hay solicitudes registradas.</td></tr>'
      : novedades.map((n) => `
        <tr>
          <td>${escapar(n.nombres)} ${escapar(n.apellidos)}</td>
          <td>${escapar(n.tipo)}</td>
          <td>${escapar(n.fecha_inicio)}</td>
          <td>${escapar(n.fecha_fin)}</td>
          <td><span class="badge ${String(n.estado || '').toLowerCase()}">${escapar(n.estado)}</span></td>
          <td>${n.estado === 'PENDIENTE' ? `
            <button class="link-approve" data-aprobar="${n.id_novedad}">Aprobar</button>
            <button class="link-danger" data-rechazar="${n.id_novedad}">Rechazar</button>
          ` : ''}</td>
        </tr>
      `).join('');
  } catch (err) {
    tabla.innerHTML = `<tr class="empty-row"><td colspan="6">${escapar(err.message)}</td></tr>`;
  }
}

document.getElementById('form-novedad').addEventListener('submit', async (evento) => {
  evento.preventDefault();
  const form = evento.target;
  const datos = Object.fromEntries(new FormData(form).entries());

  try {
    const resultado = await post('novedades', datos);
    mostrarMensaje('msg-novedad', resultado.mensaje, 'ok');
    form.reset();
    cargarNovedades();
  } catch (err) {
    mostrarMensaje('msg-novedad', err.message, 'error');
  }
});

document.getElementById('tabla-novedades').addEventListener('click', async (evento) => {
  const idAprobar = evento.target.dataset.aprobar;
  const idRechazar = evento.target.dataset.rechazar;
  if (!idAprobar && !idRechazar) return;

  const id_novedad = idAprobar || idRechazar;
  const estado = idAprobar ? 'APROBADA' : 'RECHAZADA';

  try {
    await post('novedades/estado', { id_novedad, estado });
    cargarNovedades();
  } catch (err) {
    alert(err.message);
  }
});

// ---------------------------------------------------------------
// Carga inicial
// ---------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  const hoy = new Date();
  document.getElementById('ext-fecha').value = hoy.toISOString().slice(0, 10);
  const primerDia = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
  document.getElementById('per-inicio').value = primerDia.toISOString().slice(0, 10);
  document.getElementById('per-fin').value = hoy.toISOString().slice(0, 10);

  cargarEmpleados();
  cargarPeriodos();
  cargarExtras();
  cargarConceptos();
  cargarNovedades();
});

const API = '/api/inventario';
const raiz = document.querySelector('.inventario');
const puedeEditar = raiz.dataset.puedeEditar === 'si';
let productos = [];

function escapar(valor) {
  return String(valor ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

function formatoMoneda(valor) {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 2,
  }).format(valor);
}

function mostrarMensaje(id, texto, tipo) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = texto;
  el.className = `msg show ${tipo}`;
  setTimeout(() => el.classList.remove('show'), 4000);
}

async function llamarApi(endpoint, opciones = {}) {
  const respuesta = await fetch(`${API}/${endpoint}`, opciones);
  let datos = {};
  try {
    datos = await respuesta.json();
  } catch (_e) {
    // La respuesta no era JSON (p. ej. la sesión expiró).
  }
  if (respuesta.status === 401) {
    window.location.href = '/login';
    throw new Error('Tu sesión expiró.');
  }
  if (!respuesta.ok) {
    throw new Error(datos.error || 'Ocurrió un error inesperado.');
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

// ---------------- Pestañas ----------------
document.querySelectorAll('.inventario .tab').forEach((boton) => {
  boton.addEventListener('click', () => {
    document.querySelectorAll('.inventario .tab').forEach((b) => b.classList.remove('active'));
    document.querySelectorAll('.inventario .view').forEach((v) => v.classList.remove('active'));
    boton.classList.add('active');
    document.getElementById(`view-${boton.dataset.view}`).classList.add('active');
  });
});

// ---------------- Indicadores ----------------
async function cargarResumen() {
  try {
    const r = await llamarApi('resumen');
    document.getElementById('kpi-productos').textContent = r.productos_activos;
    document.getElementById('kpi-unidades').textContent = new Intl.NumberFormat('es-CO').format(r.unidades);
    document.getElementById('kpi-costo').textContent = formatoMoneda(r.valor_costo);
    document.getElementById('kpi-venta').textContent = formatoMoneda(r.valor_venta);
    document.getElementById('kpi-bajo').textContent = r.bajo_stock;
    document.getElementById('kpi-agotados').textContent = r.agotados;
  } catch (_err) {
    // Los indicadores son informativos.
  }
}

// ---------------- Productos ----------------
function etiquetaStock(p) {
  if (p.stock_actual === 0) return '<span class="badge agotado">Agotado</span>';
  if (p.stock_actual <= p.stock_minimo) return '<span class="badge bajo">Stock bajo</span>';
  return '';
}

async function cargarProductos() {
  const tabla = document.getElementById('tabla-productos');
  const params = new URLSearchParams();
  const buscar = document.getElementById('filtro-buscar').value.trim();
  const estado = document.getElementById('filtro-estado').value;
  if (buscar) params.set('buscar', buscar);
  if (estado) params.set('estado', estado);
  if (document.getElementById('filtro-bajo').checked) params.set('bajo_stock', '1');

  try {
    productos = await llamarApi(`productos?${params}`);

    if (productos.length === 0) {
      tabla.innerHTML = '<tr class="empty-row"><td colspan="8">No hay productos que coincidan.</td></tr>';
    } else {
      tabla.innerHTML = productos.map((p) => `
        <tr>
          <td>${escapar(p.codigo)}</td>
          <td>${escapar(p.nombre)}<br><span class="hint">${escapar(p.descripcion || '')}</span></td>
          <td>${escapar(p.categoria || '—')}</td>
          <td class="num">${p.stock_actual} ${escapar(p.unidad)} ${etiquetaStock(p)}</td>
          <td class="num">${formatoMoneda(p.costo_promedio)}</td>
          <td class="num">${formatoMoneda(p.precio_venta)}</td>
          <td><span class="badge ${p.activo ? 'activo' : 'inactivo'}">${p.activo ? 'ACTIVO' : 'INACTIVO'}</span></td>
          <td>${puedeEditar ? `
            <button class="link-edit" data-editar="${p.id_producto}">Editar</button>
            ${p.activo
              ? `<button class="link-danger" data-desactivar="${p.id_producto}">Desactivar</button>`
              : `<button class="link-approve" data-activar="${p.id_producto}">Activar</button>`}
          ` : ''}</td>
        </tr>
      `).join('');
    }
  } catch (err) {
    tabla.innerHTML = `<tr class="empty-row"><td colspan="8">${escapar(err.message)}</td></tr>`;
  }
}

async function cargarSelectsProductos() {
  try {
    const activos = await llamarApi('productos?estado=ACTIVO');
    window.__activos = activos;

    const select = document.getElementById('mov-producto');
    if (select) {
      const actual = select.value;
      select.innerHTML = activos.length
        ? activos.map((p) => `<option value="${p.id_producto}">${escapar(p.codigo)} — ${escapar(p.nombre)}</option>`).join('')
        : '<option value="">No hay productos activos</option>';
      if (actual) select.value = actual;
      actualizarFormMovimiento();
    }

    const filtro = document.getElementById('filtro-mov-producto');
    const previo = filtro.value;
    filtro.innerHTML = '<option value="">Todos los productos</option>'
      + activos.map((p) => `<option value="${p.id_producto}">${escapar(p.codigo)} — ${escapar(p.nombre)}</option>`).join('');
    filtro.value = previo;
  } catch (_err) {
    // El error se muestra en la tabla principal.
  }
}

['filtro-buscar', 'filtro-estado', 'filtro-bajo'].forEach((id) => {
  const el = document.getElementById(id);
  el.addEventListener(id === 'filtro-buscar' ? 'input' : 'change', () => {
    clearTimeout(window.__debounce);
    window.__debounce = setTimeout(cargarProductos, 250);
  });
});

const formProducto = document.getElementById('form-producto');

function salirModoEdicion() {
  formProducto.reset();
  document.getElementById('prod-id').value = '';
  document.getElementById('titulo-form-producto').textContent = 'Registrar producto';
  document.getElementById('btn-guardar-producto').textContent = 'Registrar producto';
  document.getElementById('btn-cancelar-edicion').classList.add('hidden');
  formProducto.querySelectorAll('[data-solo-nuevo]').forEach((c) => c.classList.remove('hidden'));
}

function entrarModoEdicion(p) {
  document.getElementById('prod-id').value = p.id_producto;
  document.getElementById('prod-codigo').value = p.codigo;
  document.getElementById('prod-nombre').value = p.nombre;
  document.getElementById('prod-categoria').value = p.categoria || '';
  document.getElementById('prod-unidad').value = p.unidad;
  document.getElementById('prod-precio').value = p.precio_venta;
  document.getElementById('prod-minimo').value = p.stock_minimo;
  document.getElementById('prod-descripcion').value = p.descripcion || '';
  document.getElementById('titulo-form-producto').textContent = `Editar producto ${p.codigo}`;
  document.getElementById('btn-guardar-producto').textContent = 'Guardar cambios';
  document.getElementById('btn-cancelar-edicion').classList.remove('hidden');
  // El stock y el costo solo cambian con movimientos.
  formProducto.querySelectorAll('[data-solo-nuevo]').forEach((c) => c.classList.add('hidden'));
  formProducto.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

if (puedeEditar) {
  formProducto.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const datos = Object.fromEntries(new FormData(formProducto).entries());
    const editando = Boolean(datos.id_producto);

    try {
      const resultado = await post(editando ? 'productos/actualizar' : 'productos', datos);
      mostrarMensaje('msg-producto', resultado.mensaje, 'ok');
      salirModoEdicion();
      refrescarTodo();
    } catch (err) {
      mostrarMensaje('msg-producto', err.message, 'error');
    }
  });

  document.getElementById('btn-cancelar-edicion').addEventListener('click', salirModoEdicion);
}

document.getElementById('tabla-productos').addEventListener('click', async (evento) => {
  const d = evento.target.dataset;

  if (d.editar) {
    const p = productos.find((x) => String(x.id_producto) === d.editar);
    if (p) entrarModoEdicion(p);
    return;
  }

  const id = d.desactivar || d.activar;
  if (!id) return;
  if (d.desactivar && !confirm('¿Desactivar este producto? Conservará su historial pero no admitirá movimientos.')) return;

  try {
    await post('productos/estado', { id_producto: id, activo: Boolean(d.activar) });
    refrescarTodo();
  } catch (err) {
    alert(err.message);
  }
});

// ---------------- Movimientos ----------------
const formMov = document.getElementById('form-movimiento');

function actualizarFormMovimiento() {
  if (!formMov) return;
  const tipo = document.getElementById('mov-tipo').value;
  const producto = (window.__activos || []).find(
    (p) => String(p.id_producto) === document.getElementById('mov-producto').value,
  );

  document.getElementById('campo-costo').classList.toggle('hidden', tipo !== 'ENTRADA');
  document.getElementById('campo-precio').classList.toggle('hidden', tipo !== 'VENTA');
  document.getElementById('lbl-cantidad').textContent = tipo === 'AJUSTE' ? 'Conteo físico real' : 'Cantidad';
  document.getElementById('lbl-motivo').textContent =
    (tipo === 'SALIDA' || tipo === 'AJUSTE') ? 'Motivo (obligatorio)' : 'Motivo (opcional)';
  document.getElementById('mov-motivo').required = tipo === 'SALIDA' || tipo === 'AJUSTE';
  document.getElementById('hint-stock').textContent = producto
    ? `Stock actual: ${producto.stock_actual} ${producto.unidad}` : '';

  if (producto && tipo === 'VENTA') document.getElementById('mov-precio').placeholder = producto.precio_venta;
  if (producto && tipo === 'ENTRADA') document.getElementById('mov-costo').placeholder = producto.costo_promedio;
}

async function cargarMovimientos() {
  const tabla = document.getElementById('tabla-movimientos');
  const id = document.getElementById('filtro-mov-producto').value;
  try {
    const movs = await llamarApi(`movimientos${id ? `?id_producto=${encodeURIComponent(id)}` : ''}`);

    tabla.innerHTML = movs.length === 0
      ? '<tr class="empty-row"><td colspan="8">Aún no hay movimientos registrados.</td></tr>'
      : movs.map((m) => `
        <tr>
          <td>${escapar(m.fecha)}</td>
          <td>${escapar(m.codigo)} — ${escapar(m.producto)}</td>
          <td><span class="badge ${m.tipo.toLowerCase()}">${m.tipo}</span></td>
          <td class="num ${m.cantidad >= 0 ? 'pos' : 'neg'}">${m.cantidad > 0 ? '+' : ''}${m.cantidad}</td>
          <td class="num">${m.stock_resultante}</td>
          <td class="num">${formatoMoneda(m.tipo === 'VENTA' ? m.precio_unitario : m.costo_unitario)}</td>
          <td>${escapar(m.motivo || '—')}</td>
          <td>${escapar(m.usuario || '—')}</td>
        </tr>
      `).join('');
  } catch (err) {
    tabla.innerHTML = `<tr class="empty-row"><td colspan="8">${escapar(err.message)}</td></tr>`;
  }
}

document.getElementById('filtro-mov-producto').addEventListener('change', cargarMovimientos);

if (formMov) {
  document.getElementById('mov-tipo').addEventListener('change', actualizarFormMovimiento);
  document.getElementById('mov-producto').addEventListener('change', actualizarFormMovimiento);

  formMov.addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const datos = Object.fromEntries(new FormData(formMov).entries());
    if (datos.tipo !== 'ENTRADA') delete datos.costo_unitario;
    if (datos.tipo !== 'VENTA') delete datos.precio_unitario;

    try {
      const resultado = await post('movimientos', datos);
      mostrarMensaje('msg-movimiento', `${resultado.mensaje} Stock resultante: ${resultado.stock_resultante}.`, 'ok');
      formMov.reset();
      refrescarTodo();
    } catch (err) {
      mostrarMensaje('msg-movimiento', err.message, 'error');
    }
  });
}

// ---------------- Arranque ----------------
function refrescarTodo() {
  cargarResumen();
  cargarProductos();
  cargarSelectsProductos();
  cargarMovimientos();
}

refrescarTodo();
-- ============================================================================
--  EXODUS CONTABLE - ESQUEMA COMPLETO DE LA BASE DE DATOS
-- ============================================================================
--  Una sola base para todo el proyecto: contabilidad, inventario, nómina y
--  configuración (usuarios, roles, etiquetas y parámetros).
--
--  Este archivo se puede importar completo desde phpMyAdmin/HeidiSQL o dejar
--  que la aplicación lo aplique sola al arrancar (database/init_db.py).
--
--  Es seguro ejecutarlo varias veces: usa CREATE TABLE IF NOT EXISTS e
--  INSERT IGNORE / INSERT ... WHERE NOT EXISTS, así que no borra datos.
--
--  Los usuarios de demostración NO se crean aquí. La aplicación los crea la
--  primera vez (si EXODUS_DEMO no es "0") o con:
--      python run.py --crear-admin USUARIO CLAVE "Nombre completo"
-- ============================================================================

CREATE DATABASE IF NOT EXISTS `sistema_contable`
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `sistema_contable`;

-- ----------------------------------------------------------------------------
-- Usuarios y control de acceso
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `usuarios` (
  `id_usuario` int(11) NOT NULL AUTO_INCREMENT,
  `usuario` varchar(50) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `clave_hash` varchar(255) NOT NULL,
  `rol` enum('Administrador','Contador','Auxiliar','Empleado','Recursos Humanos')
         NOT NULL DEFAULT 'Empleado',
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `usuario` (`usuario`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `roles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) NOT NULL,
  `descripcion` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `permisos` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(80) NOT NULL,
  `descripcion` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `rol_permiso` (
  `rol_id` int(11) NOT NULL,
  `permiso_id` int(11) NOT NULL,
  PRIMARY KEY (`rol_id`,`permiso_id`),
  KEY `permiso_id` (`permiso_id`),
  CONSTRAINT `rol_permiso_ibfk_1` FOREIGN KEY (`rol_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE,
  CONSTRAINT `rol_permiso_ibfk_2` FOREIGN KEY (`permiso_id`) REFERENCES `permisos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `intentos_login` (
  `usuario` varchar(50) NOT NULL,
  `ip` varchar(45) NOT NULL,
  `fallos` int(11) NOT NULL DEFAULT 0,
  `bloqueado_hasta` datetime DEFAULT NULL,
  `actualizado_en` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`usuario`,`ip`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------------------------------------------------------
-- Catálogo contable (etiquetas y parámetros)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `etiquetas` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(80) NOT NULL,
  `tipo` varchar(20) NOT NULL DEFAULT 'producto',
  `porcentaje` decimal(5,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `parametros` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(80) NOT NULL,
  `etiqueta_id` int(11) NOT NULL,
  `valor` varchar(255) NOT NULL,
  `descripcion` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nombre` (`nombre`),
  KEY `etiqueta_id` (`etiqueta_id`),
  CONSTRAINT `parametros_ibfk_1` FOREIGN KEY (`etiqueta_id`) REFERENCES `etiquetas` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------------------------------------------------------
-- Contabilidad: gastos deducibles
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `gastos_deducibles` (
  `id_gasto` int(11) NOT NULL AUTO_INCREMENT,
  `descripcion` varchar(255) NOT NULL,
  `categoria` varchar(80) DEFAULT NULL,
  `tercero` varchar(150) DEFAULT NULL,
  `nit` varchar(30) DEFAULT NULL,
  `numero_documento` varchar(50) DEFAULT NULL,
  `monto` decimal(12,2) NOT NULL,
  `fecha` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `id_usuario` int(11) NOT NULL,
  `estado_gasto` enum('ACTIVO','ANULADO') NOT NULL DEFAULT 'ACTIVO',
  PRIMARY KEY (`id_gasto`),
  KEY `fk_gastos_usuarios` (`id_usuario`),
  CONSTRAINT `fk_gastos_usuarios` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------------------------------------------------------
-- Contabilidad: catálogo PUC, terceros y comprobantes
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `puc_cuentas` (
  `id_cuenta` int(11) NOT NULL AUTO_INCREMENT,
  `codigo` varchar(20) NOT NULL,
  `nombre` varchar(220) NOT NULL,
  `nivel` tinyint(4) NOT NULL DEFAULT 4,
  `clase` char(1) NOT NULL,
  `grupo` varchar(150) DEFAULT NULL,
  `naturaleza` enum('DEBITO','CREDITO') NOT NULL DEFAULT 'DEBITO',
  `es_movimiento` tinyint(1) NOT NULL DEFAULT 1,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  `creado_en` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_cuenta`),
  UNIQUE KEY `uq_puc_codigo` (`codigo`),
  KEY `idx_puc_clase` (`clase`),
  KEY `idx_puc_nombre` (`nombre`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `terceros` (
  `id_tercero` int(11) NOT NULL AUTO_INCREMENT,
  `tipo_documento` varchar(10) NOT NULL DEFAULT 'CC',
  `numero_documento` varchar(30) NOT NULL,
  `nombre` varchar(180) NOT NULL,
  `direccion` varchar(200) DEFAULT NULL,
  `ciudad` varchar(80) DEFAULT NULL,
  `email` varchar(120) DEFAULT NULL,
  `telefono` varchar(30) DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  `creado_en` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_tercero`),
  UNIQUE KEY `uq_tercero_documento` (`tipo_documento`, `numero_documento`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `comprobantes` (
  `id_comprobante` int(11) NOT NULL AUTO_INCREMENT,
  `numero` varchar(40) NOT NULL,
  `tipo` enum('DIARIO','INGRESO','EGRESO','AJUSTE','NOMINA','CIERRE') NOT NULL DEFAULT 'DIARIO',
  `fecha` date NOT NULL,
  `descripcion` varchar(255) NOT NULL,
  `id_tercero` int(11) DEFAULT NULL,
  `id_usuario` int(11) DEFAULT NULL,
  `estado` enum('BORRADOR','CONTABILIZADO','ANULADO') NOT NULL DEFAULT 'CONTABILIZADO',
  `origen` enum('MANUAL','NOMINA','INVENTARIO','CIERRE') NOT NULL DEFAULT 'MANUAL',
  `id_origen` varchar(40) DEFAULT NULL,
  `total_debito` decimal(16,2) NOT NULL DEFAULT 0.00,
  `total_credito` decimal(16,2) NOT NULL DEFAULT 0.00,
  `creado_en` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_comprobante`),
  UNIQUE KEY `uq_comprobante_numero` (`numero`),
  KEY `idx_comprobante_fecha` (`fecha`),
  KEY `idx_comprobante_estado` (`estado`),
  KEY `fk_comprobante_tercero` (`id_tercero`),
  KEY `fk_comprobante_usuario` (`id_usuario`),
  CONSTRAINT `fk_comprobante_tercero` FOREIGN KEY (`id_tercero`) REFERENCES `terceros` (`id_tercero`) ON DELETE SET NULL,
  CONSTRAINT `fk_comprobante_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `comprobante_detalle` (
  `id_detalle` int(11) NOT NULL AUTO_INCREMENT,
  `id_comprobante` int(11) NOT NULL,
  `id_cuenta` int(11) NOT NULL,
  `id_tercero` int(11) DEFAULT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `debito` decimal(16,2) NOT NULL DEFAULT 0.00,
  `credito` decimal(16,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`id_detalle`),
  KEY `idx_detalle_comprobante` (`id_comprobante`),
  KEY `idx_detalle_cuenta` (`id_cuenta`),
  KEY `fk_detalle_tercero` (`id_tercero`),
  CONSTRAINT `fk_detalle_comprobante` FOREIGN KEY (`id_comprobante`) REFERENCES `comprobantes` (`id_comprobante`) ON DELETE CASCADE,
  CONSTRAINT `fk_detalle_cuenta` FOREIGN KEY (`id_cuenta`) REFERENCES `puc_cuentas` (`id_cuenta`),
  CONSTRAINT `fk_detalle_tercero` FOREIGN KEY (`id_tercero`) REFERENCES `terceros` (`id_tercero`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------------------------------------------------------
-- Inventario
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `productos` (
  `id_producto` int(11) NOT NULL AUTO_INCREMENT,
  `codigo` varchar(40) NOT NULL,
  `nombre` varchar(150) NOT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `categoria` varchar(80) DEFAULT NULL,
  `id_etiqueta` int(11) DEFAULT NULL,
  `unidad` varchar(20) NOT NULL DEFAULT 'und',
  `costo_promedio` decimal(12,2) NOT NULL DEFAULT 0.00,
  `precio_venta` decimal(12,2) NOT NULL DEFAULT 0.00,
  `stock_actual` int(11) NOT NULL DEFAULT 0,
  `stock_minimo` int(11) NOT NULL DEFAULT 0,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  `creado_en` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_producto`),
  UNIQUE KEY `codigo` (`codigo`),
  KEY `idx_producto_etiqueta` (`id_etiqueta`),
  CONSTRAINT `fk_producto_etiqueta` FOREIGN KEY (`id_etiqueta`) REFERENCES `etiquetas` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `ventas_inventario` (
  `id_venta` int(11) NOT NULL AUTO_INCREMENT,
  `monto_total` decimal(12,2) NOT NULL,
  `costo_ventas` decimal(12,2) NOT NULL,
  `fecha` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_venta`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `movimientos_inventario` (
  `id_movimiento` int(11) NOT NULL AUTO_INCREMENT,
  `id_producto` int(11) NOT NULL,
  `tipo` enum('ENTRADA','VENTA','SALIDA','AJUSTE') NOT NULL,
  `cantidad` int(11) NOT NULL,
  `stock_resultante` int(11) NOT NULL,
  `costo_unitario` decimal(12,2) NOT NULL DEFAULT 0.00,
  `precio_unitario` decimal(12,2) DEFAULT NULL,
  `motivo` varchar(255) DEFAULT NULL,
  `id_venta` int(11) DEFAULT NULL,
  `id_usuario` int(11) DEFAULT NULL,
  `fecha` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_movimiento`),
  KEY `idx_mov_producto` (`id_producto`),
  KEY `idx_mov_fecha` (`fecha`),
  CONSTRAINT `fk_mov_producto` FOREIGN KEY (`id_producto`) REFERENCES `productos` (`id_producto`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------------------------------------------------------
-- Nómina
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `empleados` (
  `id_empleado` int(11) NOT NULL AUTO_INCREMENT,
  `nombres` varchar(100) NOT NULL,
  `apellidos` varchar(100) NOT NULL,
  `documento` varchar(30) NOT NULL,
  `tipo_documento` varchar(10) NOT NULL DEFAULT 'CC',
  `cargo` varchar(100) DEFAULT NULL,
  `email` varchar(120) DEFAULT NULL,
  `telefono` varchar(30) DEFAULT NULL,
  `direccion` varchar(200) DEFAULT NULL,
  `ciudad` varchar(80) DEFAULT NULL,
  `fecha_nacimiento` date DEFAULT NULL,
  `sexo` enum('M','F','OTRO') DEFAULT NULL,
  `estado_civil` varchar(30) DEFAULT NULL,
  `tipo_contrato` enum('INDEFINIDO','FIJO','OBRA_LABOR','APRENDIZAJE','PRESTACION_SERVICIOS') NOT NULL DEFAULT 'INDEFINIDO',
  `fecha_ingreso` date NOT NULL,
  `fecha_retiro` date DEFAULT NULL,
  `salario_base` decimal(12,2) NOT NULL,
  `salario_integral` tinyint(1) NOT NULL DEFAULT 0,
  `auxilio_transporte` decimal(12,2) DEFAULT NULL,
  `riesgo_arl` tinyint(4) NOT NULL DEFAULT 1,
  `exonerado_salud` tinyint(1) NOT NULL DEFAULT 0,
  `exonerado_parafiscales` tinyint(1) NOT NULL DEFAULT 0,
  `centro_costo` varchar(80) DEFAULT NULL,
  `banco` varchar(80) DEFAULT NULL,
  `cuenta_banco` varchar(50) DEFAULT NULL,
  `dependientes` int(11) NOT NULL DEFAULT 0,
  `estado` enum('ACTIVO','INACTIVO') NOT NULL DEFAULT 'ACTIVO',
  `creado_en` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_empleado`),
  UNIQUE KEY `documento` (`documento`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `deducciones` (
  `id_deduccion` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `porcentaje` decimal(6,3) NOT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id_deduccion`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `aportes` (
  `id_aporte` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `porcentaje` decimal(6,3) NOT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id_aporte`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `nomina` (
  `id_nomina` int(11) NOT NULL AUTO_INCREMENT,
  `id_empleado` int(11) NOT NULL,
  `periodo` varchar(7) NOT NULL,
  `salario_base` decimal(12,2) NOT NULL,
  `total_deducciones` decimal(12,2) NOT NULL,
  `total_aportes` decimal(12,2) NOT NULL,
  `salario_neto` decimal(12,2) NOT NULL,
  `generado_en` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_nomina`),
  KEY `fk_nomina_empleado` (`id_empleado`),
  CONSTRAINT `fk_nomina_empleado` FOREIGN KEY (`id_empleado`) REFERENCES `empleados` (`id_empleado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `novedades` (
  `id_novedad` int(11) NOT NULL AUTO_INCREMENT,
  `id_empleado` int(11) NOT NULL,
  `tipo` enum('AUSENCIA','VACACIONES','PERMISO') NOT NULL,
  `fecha_inicio` date NOT NULL,
  `fecha_fin` date NOT NULL,
  `motivo` varchar(255) DEFAULT NULL,
  `estado` enum('PENDIENTE','APROBADA','RECHAZADA') NOT NULL DEFAULT 'PENDIENTE',
  `creado_en` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_novedad`),
  KEY `fk_novedad_empleado` (`id_empleado`),
  CONSTRAINT `fk_novedad_empleado` FOREIGN KEY (`id_empleado`) REFERENCES `empleados` (`id_empleado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `pagos_nomina` (
  `id_pago` int(11) NOT NULL AUTO_INCREMENT,
  `total_devengado` decimal(12,2) NOT NULL,
  `total_deducciones` decimal(12,2) NOT NULL,
  `costo_patronal` decimal(12,2) NOT NULL,
  `fecha_pago` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_pago`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------------------------------------------------------
-- Nómina: parámetros legales, conceptos, novedades y liquidación por periodo
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `parametros_nomina` (
  `id_parametro` int(11) NOT NULL AUTO_INCREMENT,
  `clave` varchar(80) NOT NULL,
  `valor` decimal(16,4) NOT NULL DEFAULT 0.0000,
  `unidad` enum('PORCENTAJE','VALOR','FACTOR','HORAS','SMMLV','UVT') NOT NULL DEFAULT 'VALOR',
  `descripcion` varchar(255) DEFAULT NULL,
  `vigencia_desde` date DEFAULT NULL,
  `vigencia_hasta` date DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  `actualizado_en` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_parametro`),
  UNIQUE KEY `uq_parametro_nomina` (`clave`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `conceptos_nomina` (
  `id_concepto` int(11) NOT NULL AUTO_INCREMENT,
  `codigo` varchar(40) NOT NULL,
  `nombre` varchar(120) NOT NULL,
  `tipo` enum('DEVENGADO','DEDUCCION','APORTE_PATRONAL','PROVISION','PAGO') NOT NULL,
  `base` enum('FIJO','SALARIO','IBC','TOTAL_DEVENGADO','AUXILIO_TRANSPORTE','NETO','HORAS') NOT NULL DEFAULT 'FIJO',
  `porcentaje` decimal(8,4) NOT NULL DEFAULT 0.0000,
  `cuenta_puc` varchar(20) DEFAULT NULL,
  `cuenta_puc_credito` varchar(20) DEFAULT NULL,
  `afecta_ibc` tinyint(1) NOT NULL DEFAULT 0,
  `afecta_retencion` tinyint(1) NOT NULL DEFAULT 0,
  `es_provision` tinyint(1) NOT NULL DEFAULT 0,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  `orden` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id_concepto`),
  UNIQUE KEY `uq_concepto_codigo` (`codigo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `novedades_nomina` (
  `id_novedad_nomina` int(11) NOT NULL AUTO_INCREMENT,
  `id_empleado` int(11) NOT NULL,
  `concepto_codigo` varchar(40) NOT NULL,
  `fecha` date NOT NULL,
  `cantidad` decimal(12,4) NOT NULL DEFAULT 0.0000,
  `valor_unitario` decimal(14,2) DEFAULT NULL,
  `valor_total` decimal(14,2) DEFAULT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `aplica_ibc` tinyint(1) DEFAULT NULL,
  `aplica_retencion` tinyint(1) DEFAULT NULL,
  `estado` enum('ACTIVA','ANULADA') NOT NULL DEFAULT 'ACTIVA',
  `id_usuario` int(11) DEFAULT NULL,
  `creado_en` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_novedad_nomina`),
  KEY `idx_novedad_nomina_empleado` (`id_empleado`),
  KEY `idx_novedad_nomina_fecha` (`fecha`),
  KEY `fk_novedad_nomina_concepto` (`concepto_codigo`),
  KEY `fk_novedad_nomina_usuario` (`id_usuario`),
  CONSTRAINT `fk_novedad_nomina_empleado` FOREIGN KEY (`id_empleado`) REFERENCES `empleados` (`id_empleado`) ON DELETE CASCADE,
  CONSTRAINT `fk_novedad_nomina_concepto` FOREIGN KEY (`concepto_codigo`) REFERENCES `conceptos_nomina` (`codigo`) ON UPDATE CASCADE,
  CONSTRAINT `fk_novedad_nomina_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `nomina_periodos` (
  `id_periodo` int(11) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(120) NOT NULL,
  `tipo` enum('MENSUAL','QUINCENAL','SEMANAL','PRIMA','CESANTIAS','VACACIONES','OTRO') NOT NULL DEFAULT 'MENSUAL',
  `fecha_inicio` date NOT NULL,
  `fecha_fin` date NOT NULL,
  `fecha_pago` date DEFAULT NULL,
  `estado` enum('BORRADOR','CALCULADO','CONTABILIZADO','PAGADO','ANULADO') NOT NULL DEFAULT 'CALCULADO',
  `total_devengado` decimal(16,2) NOT NULL DEFAULT 0.00,
  `total_deducciones` decimal(16,2) NOT NULL DEFAULT 0.00,
  `total_aportes` decimal(16,2) NOT NULL DEFAULT 0.00,
  `total_provisiones` decimal(16,2) NOT NULL DEFAULT 0.00,
  `total_neto` decimal(16,2) NOT NULL DEFAULT 0.00,
  `id_comprobante` int(11) DEFAULT NULL,
  `id_usuario` int(11) DEFAULT NULL,
  `creado_en` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_periodo`),
  UNIQUE KEY `uq_nomina_periodo` (`fecha_inicio`,`fecha_fin`,`tipo`),
  KEY `idx_nomina_periodo_estado` (`estado`),
  KEY `fk_nomina_periodo_comprobante` (`id_comprobante`),
  KEY `fk_nomina_periodo_usuario` (`id_usuario`),
  CONSTRAINT `fk_nomina_periodo_comprobante` FOREIGN KEY (`id_comprobante`) REFERENCES `comprobantes` (`id_comprobante`) ON DELETE SET NULL,
  CONSTRAINT `fk_nomina_periodo_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `nomina_detalle` (
  `id_detalle` int(11) NOT NULL AUTO_INCREMENT,
  `id_periodo` int(11) NOT NULL,
  `id_empleado` int(11) NOT NULL,
  `dias_laborados` decimal(6,2) NOT NULL DEFAULT 30.00,
  `salario_base` decimal(14,2) NOT NULL DEFAULT 0.00,
  `auxilio_transporte` decimal(14,2) NOT NULL DEFAULT 0.00,
  `total_horas_extra` decimal(14,2) NOT NULL DEFAULT 0.00,
  `total_devengado` decimal(16,2) NOT NULL DEFAULT 0.00,
  `ibc` decimal(16,2) NOT NULL DEFAULT 0.00,
  `total_deducciones` decimal(16,2) NOT NULL DEFAULT 0.00,
  `total_aportes` decimal(16,2) NOT NULL DEFAULT 0.00,
  `total_provisiones` decimal(16,2) NOT NULL DEFAULT 0.00,
  `neto_pagar` decimal(16,2) NOT NULL DEFAULT 0.00,
  PRIMARY KEY (`id_detalle`),
  UNIQUE KEY `uq_nomina_detalle` (`id_periodo`,`id_empleado`),
  KEY `idx_nomina_detalle_empleado` (`id_empleado`),
  CONSTRAINT `fk_nomina_detalle_periodo` FOREIGN KEY (`id_periodo`) REFERENCES `nomina_periodos` (`id_periodo`) ON DELETE CASCADE,
  CONSTRAINT `fk_nomina_detalle_empleado` FOREIGN KEY (`id_empleado`) REFERENCES `empleados` (`id_empleado`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `nomina_detalle_conceptos` (
  `id_detalle_concepto` int(11) NOT NULL AUTO_INCREMENT,
  `id_detalle` int(11) NOT NULL,
  `codigo_concepto` varchar(40) NOT NULL,
  `nombre` varchar(120) NOT NULL,
  `tipo` enum('DEVENGADO','DEDUCCION','APORTE_PATRONAL','PROVISION','PAGO') NOT NULL,
  `base_calculo` decimal(16,2) NOT NULL DEFAULT 0.00,
  `porcentaje` decimal(8,4) NOT NULL DEFAULT 0.0000,
  `valor` decimal(16,2) NOT NULL DEFAULT 0.00,
  `cuenta_puc` varchar(20) DEFAULT NULL,
  `cuenta_puc_credito` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id_detalle_concepto`),
  KEY `idx_detalle_concepto_detalle` (`id_detalle`),
  CONSTRAINT `fk_detalle_concepto_detalle` FOREIGN KEY (`id_detalle`) REFERENCES `nomina_detalle` (`id_detalle`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ----------------------------------------------------------------------------
-- Datos base (catálogos). No incluye usuarios ni movimientos de ejemplo.
-- ----------------------------------------------------------------------------
INSERT IGNORE INTO `roles` (`nombre`, `descripcion`) VALUES
  ('Administrador', 'Acceso total al sistema'),
  ('Contador', 'Gestión contable y reportes'),
  ('Auxiliar', 'Apoyo contable y de inventario'),
  ('Empleado', 'Acceso básico de consulta'),
  ('Recursos Humanos', 'Gestión de nómina y empleados');

INSERT IGNORE INTO `permisos` (`nombre`, `descripcion`) VALUES
  ('ver_inicio', 'Ver página de inicio'),
  ('ver_inventario', 'Ver módulo de inventario'),
  ('ver_nomina', 'Ver módulo de nómina'),
  ('ver_contabilidad', 'Ver módulo de contabilidad'),
  ('ver_configuracion', 'Ver módulo de configuración'),
  ('gestionar_usuarios', 'Crear, editar y eliminar usuarios'),
  ('gestionar_roles', 'Crear, editar y eliminar roles'),
  ('gestionar_etiquetas', 'Crear, editar y eliminar etiquetas'),
  ('gestionar_parametros', 'Crear, editar y eliminar parámetros');

-- Administrador: todos los permisos
INSERT IGNORE INTO `rol_permiso` (`rol_id`, `permiso_id`)
  SELECT r.id, p.id FROM roles r CROSS JOIN permisos p
   WHERE r.nombre = 'Administrador';

-- Contador
INSERT IGNORE INTO `rol_permiso` (`rol_id`, `permiso_id`)
  SELECT r.id, p.id FROM roles r JOIN permisos p
    ON p.nombre IN ('ver_inicio','ver_contabilidad','ver_configuracion',
                    'gestionar_etiquetas','gestionar_parametros')
   WHERE r.nombre = 'Contador';

-- Auxiliar
INSERT IGNORE INTO `rol_permiso` (`rol_id`, `permiso_id`)
  SELECT r.id, p.id FROM roles r JOIN permisos p
    ON p.nombre IN ('ver_inicio','ver_inventario','ver_nomina')
   WHERE r.nombre = 'Auxiliar';

-- Empleado
INSERT IGNORE INTO `rol_permiso` (`rol_id`, `permiso_id`)
  SELECT r.id, p.id FROM roles r JOIN permisos p
    ON p.nombre IN ('ver_inicio')
   WHERE r.nombre = 'Empleado';

-- Recursos Humanos
INSERT IGNORE INTO `rol_permiso` (`rol_id`, `permiso_id`)
  SELECT r.id, p.id FROM roles r JOIN permisos p
    ON p.nombre IN ('ver_inicio','ver_nomina','ver_inventario')
   WHERE r.nombre = 'Recursos Humanos';

INSERT IGNORE INTO `etiquetas` (`nombre`, `tipo`, `porcentaje`) VALUES
  ('General', 'producto', 0.00),
  ('IVA 19%', 'impuesto', 19.00);

INSERT INTO `deducciones` (`nombre`, `porcentaje`)
  SELECT 'Salud (empleado)', 4.000 FROM DUAL
   WHERE NOT EXISTS (SELECT 1 FROM deducciones WHERE nombre = 'Salud (empleado)');
INSERT INTO `deducciones` (`nombre`, `porcentaje`)
  SELECT 'Pensión (empleado)', 4.000 FROM DUAL
   WHERE NOT EXISTS (SELECT 1 FROM deducciones WHERE nombre = 'Pensión (empleado)');

INSERT INTO `aportes` (`nombre`, `porcentaje`)
  SELECT 'Salud (empleador)', 8.500 FROM DUAL
   WHERE NOT EXISTS (SELECT 1 FROM aportes WHERE nombre = 'Salud (empleador)');
INSERT INTO `aportes` (`nombre`, `porcentaje`)
  SELECT 'Pensión (empleador)', 12.000 FROM DUAL
   WHERE NOT EXISTS (SELECT 1 FROM aportes WHERE nombre = 'Pensión (empleador)');
INSERT INTO `aportes` (`nombre`, `porcentaje`)
  SELECT 'ARL', 0.522 FROM DUAL
   WHERE NOT EXISTS (SELECT 1 FROM aportes WHERE nombre = 'ARL');

-- ----------------------------------------------------------------------------
-- Parámetros legales de nómina (editables desde el módulo de nómina)
-- Valores iniciales tomados del documento de liquidación (SMMLV 2025).
-- ----------------------------------------------------------------------------
INSERT IGNORE INTO `parametros_nomina` (`clave`, `valor`, `unidad`, `descripcion`) VALUES
  ('SMMLV', 1750905.0000, 'VALOR', 'Salario mínimo mensual legal vigente'),
  ('AUXILIO_TRANSPORTE', 249095.0000, 'VALOR', 'Auxilio de transporte mensual'),
  ('UVT', 52374.0000, 'VALOR', 'Unidad de valor tributario'),
  ('HORAS_MES', 210.0000, 'HORAS', 'Horas ordinarias remuneradas al mes'),
  ('SALUD_EMPLEADO', 4.0000, 'PORCENTAJE', 'Aporte a salud a cargo del empleado'),
  ('PENSION_EMPLEADO', 4.0000, 'PORCENTAJE', 'Aporte a pensión a cargo del empleado'),
  ('SALUD_EMPLEADOR', 8.5000, 'PORCENTAJE', 'Aporte a salud a cargo del empleador'),
  ('PENSION_EMPLEADOR', 12.0000, 'PORCENTAJE', 'Aporte a pensión a cargo del empleador'),
  ('SENA', 2.0000, 'PORCENTAJE', 'Aporte parafiscal SENA'),
  ('ICBF', 3.0000, 'PORCENTAJE', 'Aporte parafiscal ICBF'),
  ('CAJA_COMPENSACION', 4.0000, 'PORCENTAJE', 'Aporte a caja de compensación familiar'),
  ('PRIMA', 8.3300, 'PORCENTAJE', 'Provisión de prima de servicios'),
  ('CESANTIAS', 8.3300, 'PORCENTAJE', 'Provisión de cesantías'),
  ('INTERESES_CESANTIAS', 1.0000, 'PORCENTAJE', 'Provisión de intereses sobre cesantías'),
  ('VACACIONES', 4.1700, 'PORCENTAJE', 'Provisión de vacaciones'),
  ('ARL_NIVEL_1', 0.5220, 'PORCENTAJE', 'Tarifa ARL nivel de riesgo I'),
  ('ARL_NIVEL_2', 1.0440, 'PORCENTAJE', 'Tarifa ARL nivel de riesgo II'),
  ('ARL_NIVEL_3', 2.4360, 'PORCENTAJE', 'Tarifa ARL nivel de riesgo III'),
  ('ARL_NIVEL_4', 4.3500, 'PORCENTAJE', 'Tarifa ARL nivel de riesgo IV'),
  ('ARL_NIVEL_5', 6.9600, 'PORCENTAJE', 'Tarifa ARL nivel de riesgo V'),
  ('TOPE_AUXILIO_TRANSPORTE_SMMLV', 2.0000, 'SMMLV', 'Tope de salario para recibir auxilio de transporte'),
  ('TOPE_EXONERACION_SMMLV', 10.0000, 'SMMLV', 'Tope de salario para exoneración de salud y parafiscales'),
  ('TOPE_IBC_SMMLV', 25.0000, 'SMMLV', 'Tope máximo de la base de cotización'),
  ('FSP_UMBRAL_1_SMMLV', 4.0000, 'SMMLV', 'Umbral de ingreso para fondo de solidaridad pensional'),
  ('FSP_UMBRAL_2_SMMLV', 16.0000, 'SMMLV', 'Segundo umbral de fondo de solidaridad pensional'),
  ('FSP_UMBRAL_3_SMMLV', 17.0000, 'SMMLV', 'Tercer umbral de fondo de solidaridad pensional'),
  ('FSP_UMBRAL_4_SMMLV', 20.0000, 'SMMLV', 'Cuarto umbral de fondo de solidaridad pensional'),
  ('FSP_TASA_1', 1.0000, 'PORCENTAJE', 'Tarifa FSP entre 4 y 16 SMMLV'),
  ('FSP_TASA_2', 1.2000, 'PORCENTAJE', 'Tarifa FSP entre 16 y 17 SMMLV'),
  ('FSP_TASA_3', 1.4000, 'PORCENTAJE', 'Tarifa FSP entre 17 y 20 SMMLV'),
  ('FSP_TASA_4', 1.6000, 'PORCENTAJE', 'Tarifa FSP desde 20 SMMLV'),
  ('HED_FACTOR', 1.2500, 'FACTOR', 'Factor hora extra diurna'),
  ('HEN_FACTOR', 1.7500, 'FACTOR', 'Factor hora extra nocturna'),
  ('RNOCT_FACTOR', 0.3500, 'FACTOR', 'Recargo nocturno ordinario'),
  ('HODF_FACTOR', 1.9000, 'FACTOR', 'Factor hora ordinaria dominical o festiva'),
  ('HEDF_FACTOR', 2.1500, 'FACTOR', 'Factor hora extra diurna dominical o festiva'),
  ('HONDF_FACTOR', 2.2500, 'FACTOR', 'Factor hora ordinaria nocturna dominical o festiva'),
  ('HENDF_FACTOR', 2.6500, 'FACTOR', 'Factor hora extra nocturna dominical o festiva'),
  ('RETEFUENTE_EXENTO', 25.0000, 'PORCENTAJE', 'Renta exenta sobre renta líquida'),
  ('RETEFUENTE_TOPE_EXENTO_UVT_MES', 65.8333, 'UVT', 'Tope mensual de la renta exenta (790 UVT anuales)'),
  ('RETEFUENTE_DEPENDIENTES', 10.0000, 'PORCENTAJE', 'Deducción por dependientes económicos'),
  ('RETEFUENTE_DEPENDIENTES_TOPE_UVT_MES', 32.0000, 'UVT', 'Tope mensual de deducción por dependientes'),
  ('RETEFUENTE_DEPENDIENTES_UVT_MES', 6.0000, 'UVT', 'Deducción mensual por cada dependiente'),
  ('RETEFUENTE_PREPAGADA_TOPE_UVT_MES', 16.0000, 'UVT', 'Tope mensual de salud prepagada'),
  ('RETEFUENTE_INTERESES_TOPE_UVT_MES', 100.0000, 'UVT', 'Tope mensual de intereses de vivienda'),
  ('RETEFUENTE_APORTE_VOLUNTARIO_TOPE_UVT_MES', 380.0000, 'UVT', 'Tope mensual de aportes voluntarios a pensión'),
  ('TOPE_EMBARGO', 50.0000, 'PORCENTAJE', 'Porcentaje máximo embargable sobre el neto disponible');

-- ----------------------------------------------------------------------------
-- Conceptos de nómina y su cuenta PUC (tomados del plan de cuentas del libro)
-- ----------------------------------------------------------------------------
INSERT IGNORE INTO `conceptos_nomina`
  (`codigo`, `nombre`, `tipo`, `base`, `porcentaje`, `cuenta_puc`, `cuenta_puc_credito`, `afecta_ibc`, `afecta_retencion`, `es_provision`, `orden`) VALUES
  ('SALARIO', 'Sueldo básico', 'DEVENGADO', 'SALARIO', 0, '510506', NULL, 1, 1, 0, 10),
  ('AUX_TRANSPORTE', 'Auxilio de transporte', 'DEVENGADO', 'AUXILIO_TRANSPORTE', 0, '510527', NULL, 0, 0, 0, 20),
  ('HED', 'Horas extra diurnas', 'DEVENGADO', 'HORAS', 1.25, '510515', NULL, 1, 1, 0, 30),
  ('HEN', 'Horas extra nocturnas', 'DEVENGADO', 'HORAS', 1.75, '510515', NULL, 1, 1, 0, 31),
  ('RNOCT', 'Recargo nocturno', 'DEVENGADO', 'HORAS', 0.35, '510515', NULL, 1, 1, 0, 32),
  ('HODF', 'Horas ordinarias dominical/festivo', 'DEVENGADO', 'HORAS', 1.90, '510515', NULL, 1, 1, 0, 33),
  ('HEDF', 'Horas extra diurnas dominical/festivo', 'DEVENGADO', 'HORAS', 2.15, '510515', NULL, 1, 1, 0, 34),
  ('HONDF', 'Horas ordinarias nocturnas dominical/festivo', 'DEVENGADO', 'HORAS', 2.25, '510515', NULL, 1, 1, 0, 35),
  ('HENDF', 'Horas extra nocturnas dominical/festivo', 'DEVENGADO', 'HORAS', 2.65, '510515', NULL, 1, 1, 0, 36),
  ('BONIFICACION', 'Bonificación / incentivo', 'DEVENGADO', 'FIJO', 0, '510506', NULL, 1, 1, 0, 40),
  ('COMISION', 'Comisión', 'DEVENGADO', 'FIJO', 0, '520518', NULL, 1, 1, 0, 41),
  ('SALUD_EMPLEADO', 'Salud empleado (4%)', 'DEDUCCION', 'IBC', 4.00, '237005', NULL, 0, 1, 0, 100),
  ('PENSION_EMPLEADO', 'Pensión empleado (4%)', 'DEDUCCION', 'IBC', 4.00, '238030', NULL, 0, 1, 0, 101),
  ('FSP', 'Fondo de solidaridad pensional', 'DEDUCCION', 'IBC', 0, '238095', NULL, 0, 1, 0, 102),
  ('RETEFUENTE', 'Retención en la fuente', 'DEDUCCION', 'FIJO', 0, '236505', NULL, 0, 0, 0, 103),
  ('EMBARGO', 'Embargo judicial', 'DEDUCCION', 'NETO', 0, '237025', NULL, 0, 0, 0, 104),
  ('LIBRANZA', 'Libranza', 'DEDUCCION', 'FIJO', 0, '237030', NULL, 0, 0, 0, 105),
  ('FONDO_EMPLEADOS', 'Fondo de empleados', 'DEDUCCION', 'FIJO', 0, '237045', NULL, 0, 0, 0, 106),
  ('PRESTAMO_EMPRESA', 'Préstamo a la empresa', 'DEDUCCION', 'FIJO', 0, '136590', NULL, 0, 0, 0, 107),
  ('SINDICATO', 'Aporte sindical', 'DEDUCCION', 'FIJO', 0, '237035', NULL, 0, 0, 0, 108),
  ('PREPAGADA', 'Salud prepagada', 'DEDUCCION', 'FIJO', 0, '238095', NULL, 0, 1, 0, 109),
  ('APORTE_VOLUNTARIO', 'Aporte voluntario a pensión', 'DEDUCCION', 'FIJO', 0, '238095', NULL, 0, 1, 0, 110),
  ('SALUD_EMPLEADOR', 'Salud empleador (8.5%)', 'APORTE_PATRONAL', 'IBC', 8.50, '510569', '237005', 0, 0, 0, 200),
  ('PENSION_EMPLEADOR', 'Pensión empleador (12%)', 'APORTE_PATRONAL', 'IBC', 12.00, '510570', '238030', 0, 0, 0, 201),
  ('ARL', 'ARL', 'APORTE_PATRONAL', 'IBC', 0.522, '510568', '237006', 0, 0, 0, 202),
  ('SENA', 'SENA', 'APORTE_PATRONAL', 'IBC', 2.00, '510578', '237010', 0, 0, 0, 203),
  ('ICBF', 'ICBF', 'APORTE_PATRONAL', 'IBC', 3.00, '510575', '237010', 0, 0, 0, 204),
  ('CAJA', 'Caja de compensación familiar', 'APORTE_PATRONAL', 'IBC', 4.00, '510572', '237010', 0, 0, 0, 205),
  ('CESANTIAS', 'Cesantías', 'PROVISION', 'SALARIO', 8.33, '510530', '251010', 0, 0, 1, 300),
  ('INTERESES_CESANTIAS', 'Intereses sobre cesantías', 'PROVISION', 'SALARIO', 1.00, '510533', '251505', 0, 0, 1, 301),
  ('PRIMA', 'Prima de servicios', 'PROVISION', 'SALARIO', 8.33, '510536', '252005', 0, 0, 1, 302),
  ('VACACIONES', 'Vacaciones', 'PROVISION', 'SALARIO', 4.17, '510539', '252505', 0, 0, 1, 303),
  ('NETO', 'Neto a pagar', 'PAGO', 'NETO', 0, '250505', NULL, 0, 0, 0, 999);


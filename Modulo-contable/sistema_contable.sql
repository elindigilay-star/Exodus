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
  `cargo` varchar(100) DEFAULT NULL,
  `salario_base` decimal(12,2) NOT NULL,
  `fecha_ingreso` date NOT NULL,
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

-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 21-10-2026 a las 23:24:55
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12




--
-- Base de datos: `sistema_contable`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `aportes`
--
create DATABASE IF NOT EXISTS `sistema_contable` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `sistema_contable`;

CREATE TABLE `aportes` (
  `id_aporte` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `porcentaje` decimal(6,3) NOT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `aportes`
--

INSERT INTO `aportes` (`id_aporte`, `nombre`, `porcentaje`, `activo`) VALUES
(1, 'Salud (empleador)', 8.500, 1),
(2, 'Pensión (empleador)', 12.000, 1),
(3, 'ARL', 0.522, 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `deducciones`
--

CREATE TABLE `deducciones` (
  `id_deduccion` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `porcentaje` decimal(6,3) NOT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `deducciones`
--

INSERT INTO `deducciones` (`id_deduccion`, `nombre`, `porcentaje`, `activo`) VALUES
(1, 'Salud (empleado)', 4.000, 1),
(2, 'Pensión (empleado)', 4.000, 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `empleados`
--

CREATE TABLE `empleados` (
  `id_empleado` int(11) NOT NULL,
  `nombres` varchar(100) NOT NULL,
  `apellidos` varchar(100) NOT NULL,
  `documento` varchar(30) NOT NULL,
  `cargo` varchar(100) DEFAULT NULL,
  `salario_base` decimal(12,2) NOT NULL,
  `fecha_ingreso` date NOT NULL,
  `estado` enum('ACTIVO','INACTIVO') NOT NULL DEFAULT 'ACTIVO',
  `creado_en` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `empleados`
--

INSERT INTO `empleados` (`id_empleado`, `nombres`, `apellidos`, `documento`, `cargo`, `salario_base`, `fecha_ingreso`, `estado`, `creado_en`) VALUES
(1, 'Laura', 'Gómez', '1001234567', 'Auxiliar contable', 1800000.00, '2025-03-01', 'ACTIVO', '2026-10-14 20:22:16');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `etiquetas`
--

CREATE TABLE `etiquetas` (
  `id` int(11) NOT NULL,
  `nombre` varchar(80) NOT NULL,
  `tipo` varchar(20) NOT NULL,
  `porcentaje` decimal(5,2) NOT NULL DEFAULT 0.00
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `gastos_deducibles`
--

CREATE TABLE `gastos_deducibles` (
  `id_gasto` int(11) NOT NULL,
  `descripcion` varchar(255) NOT NULL,
  `categoria` varchar(80) DEFAULT NULL,
  `tercero` varchar(150) DEFAULT NULL,
  `nit` varchar(30) DEFAULT NULL,
  `numero_documento` varchar(50) DEFAULT NULL,
  `monto` decimal(12,2) NOT NULL,
  `fecha` datetime NOT NULL DEFAULT current_timestamp(),
  `id_usuario` int(11) NOT NULL,
  `estado_gasto` enum('ACTIVO','ANULADO') NOT NULL DEFAULT 'ACTIVO'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `gastos_deducibles`
--

INSERT INTO `gastos_deducibles` (`id_gasto`, `descripcion`, `monto`, `fecha`, `id_usuario`) VALUES
(1, 'Gasto de oficina', 250.00, '2026-10-07 16:57:00', 1),
(2, 'Servicios públicos', 180.50, '2026-09-28 16:57:00', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `movimientos_inventario`
--

CREATE TABLE `movimientos_inventario` (
  `id_movimiento` int(11) NOT NULL,
  `id_producto` int(11) NOT NULL,
  `tipo` enum('ENTRADA','VENTA','SALIDA','AJUSTE') NOT NULL,
  `cantidad` int(11) NOT NULL,
  `stock_resultante` int(11) NOT NULL,
  `costo_unitario` decimal(12,2) NOT NULL DEFAULT 0.00,
  `precio_unitario` decimal(12,2) DEFAULT NULL,
  `motivo` varchar(255) DEFAULT NULL,
  `id_venta` int(11) DEFAULT NULL,
  `id_usuario` int(11) DEFAULT NULL,
  `fecha` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `movimientos_inventario`
--

INSERT INTO `movimientos_inventario` (`id_movimiento`, `id_producto`, `tipo`, `cantidad`, `stock_resultante`, `costo_unitario`, `precio_unitario`, `motivo`, `id_venta`, `id_usuario`, `fecha`) VALUES
(1, 1, 'ENTRADA', 10, 10, 1000000.00, NULL, 'Stock inicial', NULL, NULL, '2026-10-15 21:28:46'),
(2, 2, 'ENTRADA', 5, 5, 20000.00, NULL, 'Stock inicial', NULL, NULL, '2026-10-15 21:28:46'),
(3, 1, 'VENTA', -2, 8, 1000000.00, 1500000.00, NULL, 3, 4, '2026-10-21 16:05:25'),
(4, 1, 'VENTA', -5, 3, 1000000.00, 150000.00, NULL, 4, 4, '2026-10-21 16:06:34'),
(5, 2, 'VENTA', -1, 4, 20000.00, 50000.00, NULL, 5, 4, '2026-10-21 16:23:53');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `nomina`
--

CREATE TABLE `nomina` (
  `id_nomina` int(11) NOT NULL,
  `id_empleado` int(11) NOT NULL,
  `periodo` varchar(7) NOT NULL,
  `salario_base` decimal(12,2) NOT NULL,
  `total_deducciones` decimal(12,2) NOT NULL,
  `total_aportes` decimal(12,2) NOT NULL,
  `salario_neto` decimal(12,2) NOT NULL,
  `generado_en` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `novedades`
--

CREATE TABLE `novedades` (
  `id_novedad` int(11) NOT NULL,
  `id_empleado` int(11) NOT NULL,
  `tipo` enum('AUSENCIA','VACACIONES','PERMISO') NOT NULL,
  `fecha_inicio` date NOT NULL,
  `fecha_fin` date NOT NULL,
  `motivo` varchar(255) DEFAULT NULL,
  `estado` enum('PENDIENTE','APROBADA','RECHAZADA') NOT NULL DEFAULT 'PENDIENTE',
  `creado_en` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `pagos_nomina`
--

CREATE TABLE `pagos_nomina` (
  `id_pago` int(11) NOT NULL,
  `total_devengado` decimal(12,2) NOT NULL,
  `total_deducciones` decimal(12,2) NOT NULL,
  `costo_patronal` decimal(12,2) NOT NULL,
  `fecha_pago` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `pagos_nomina`
--

INSERT INTO `pagos_nomina` (`id_pago`, `total_devengado`, `total_deducciones`, `costo_patronal`, `fecha_pago`) VALUES
(1, 12000.00, 2000.00, 3000.00, '2026-09-30 16:57:00'),
(2, 9500.00, 1500.00, 2500.00, '2026-10-06 16:57:00');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `parametros`
--

CREATE TABLE `parametros` (
  `id` int(11) NOT NULL,
  `nombre` varchar(80) NOT NULL,
  `etiqueta_id` int(11) NOT NULL,
  `valor` varchar(255) NOT NULL,
  `descripcion` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `permisos`
--

CREATE TABLE `permisos` (
  `id` int(11) NOT NULL,
  `nombre` varchar(80) NOT NULL,
  `descripcion` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `permisos`
--

INSERT INTO `permisos` (`id`, `nombre`, `descripcion`) VALUES
(1, 'ver_inicio', 'Ver página de inicio'),
(2, 'ver_inventario', 'Ver módulo de inventario'),
(3, 'ver_nomina', 'Ver módulo de nómina'),
(4, 'ver_contabilidad', 'Ver módulo de contabilidad'),
(5, 'ver_configuracion', 'Ver módulo de configuración'),
(6, 'gestionar_usuarios', 'Crear, editar y eliminar usuarios'),
(7, 'gestionar_roles', 'Crear, editar y eliminar roles'),
(8, 'gestionar_etiquetas', 'Crear, editar y eliminar etiquetas'),
(9, 'gestionar_parametros', 'Crear, editar y eliminar parámetros');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `productos`
--

CREATE TABLE `productos` (
  `id_producto` int(11) NOT NULL,
  `codigo` varchar(40) NOT NULL,
  `nombre` varchar(150) NOT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `categoria` varchar(80) DEFAULT NULL,
  `unidad` varchar(20) NOT NULL DEFAULT 'und',
  `costo_promedio` decimal(12,2) NOT NULL DEFAULT 0.00,
  `precio_venta` decimal(12,2) NOT NULL DEFAULT 0.00,
  `stock_actual` int(11) NOT NULL DEFAULT 0,
  `stock_minimo` int(11) NOT NULL DEFAULT 0,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  `creado_en` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `productos`
--

INSERT INTO `productos` (`id_producto`, `codigo`, `nombre`, `descripcion`, `categoria`, `unidad`, `costo_promedio`, `precio_venta`, `stock_actual`, `stock_minimo`, `activo`, `creado_en`) VALUES
(1, 'LAP-01', 'Laptop 15\"', NULL, 'Equipos', 'und', 1000000.00, 1500000.00, 3, 2, 1, '2026-10-16 02:28:45'),
(2, 'MOU-01', 'Mouse inalámbrico', NULL, 'Accesorios', 'und', 20000.00, 50000.00, 4, 5, 1, '2026-10-16 02:28:45');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `roles`
--

CREATE TABLE `roles` (
  `id` int(11) NOT NULL,
  `nombre` varchar(50) NOT NULL,
  `descripcion` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `roles`
--

INSERT INTO `roles` (`id`, `nombre`, `descripcion`) VALUES
(1, 'Administrador', 'Acceso total al sistema'),
(2, 'Contador', 'Gestión contable y reportes'),
(3, 'Auxiliar', 'Apoyo contable y de inventario'),
(4, 'Empleado', 'Acceso básico de consulta');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `rol_permiso`
--

CREATE TABLE `rol_permiso` (
  `rol_id` int(11) NOT NULL,
  `permiso_id` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `rol_permiso`
--

INSERT INTO `rol_permiso` (`rol_id`, `permiso_id`) VALUES
(1, 1),
(1, 2),
(1, 3),
(1, 4),
(1, 5),
(1, 6),
(1, 7),
(1, 8),
(1, 9),
(2, 1),
(2, 4),
(2, 5),
(2, 8),
(2, 9),
(3, 1),
(3, 2),
(3, 3),
(4, 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuarios`
--

CREATE TABLE `usuarios` (
  `id_usuario` int(11) NOT NULL,
  `usuario` varchar(50) DEFAULT NULL,
  `nombre` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `clave_hash` varchar(255) DEFAULT NULL,
  `rol` enum('Administrador','Contador','Auxiliar','Empleado') NOT NULL DEFAULT 'Empleado',
  `activo` tinyint(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `usuarios`
--

INSERT INTO `usuarios` (`id_usuario`, `usuario`, `nombre`, `email`, `clave_hash`, `rol`, `activo`) VALUES
(1, 'carlos', 'Carlos Pérez', 'carlos@empresa.com', 'scrypt:32768:8:1$U7IHXlRQFA1MKX36$915e887ac9f57c6fc1e93c2045d59749c234835c60c23f0570a2734ef7c612c2b87905c2d311ab5f9b75c4989f3dd1e534a96d016028f87841c7089df1118075', 'Administrador', 1),
(2, 'ana', 'Ana Gómez', 'ana@empresa.com', 'scrypt:32768:8:1$4jXaLmPXEVTH6Wiv$037c35449522856e66bb8a00c0773fbaf8cbfec0b565d25c545a18fa25c585e8323f6554e4f714c853a8053e19d1adc5cb7df419f4f6f0a3519a2eebd14e5a29', 'Contador', 1),
(3, 'juan', 'Juan Torres', 'juan@empresa.com', 'scrypt:32768:8:1$MwvRCbhswXyTfkeL$1a935780fe141e1338ad66d2ba931d83c407368ffb2423e7b99f83fc3fad80c6a06efbf0ba38caac24169f8c3a90160963911047ccb4fe97c493c29f1847a198', 'Auxiliar', 1),
(4, 'admin', 'Administrador Principal', 'admin@sistema.com', 'scrypt:32768:8:1$8v9Ldlr6SUk2pCfH$706d43ec886b113c45efe9fb67cab42bfaa74a3d74fd8d7430a830b7933d51b47d733489ab2c97ca84d816ed4725613d5cf9589fce7b440b454b3a782baecde7', 'Administrador', 1),
(5, 'contador', 'Contador Jefe', 'contador@sistema.com', 'scrypt:32768:8:1$jAwnR7AV6cpOOeGp$33bfbc17eeacad6bac77dacc8dfbd8dc28511ad75d2f92741dbdf4e0df6c063082cdd68cf0956efbb871f0f158c58fd206d9def87e1a6ffec1abc49de73c7bff', 'Contador', 1),
(6, 'auxiliar', 'Auxiliar Administrativo', 'auxiliar@sistema.com', 'scrypt:32768:8:1$RWpTl6xIY5vpo6Vv$8a7716e3a7bf9db87739256a5e164d483cd97946cee19cbe3ea261e2f9fe42c63704d1515a8f7610b771ab8729b8e4a9a8de6b14a9334e6dde1c651656853fff', 'Auxiliar', 1);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `ventas_inventario`
--

CREATE TABLE `ventas_inventario` (
  `id_venta` int(11) NOT NULL,
  `monto_total` decimal(12,2) NOT NULL,
  `costo_ventas` decimal(12,2) NOT NULL,
  `fecha` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `ventas_inventario`
--

INSERT INTO `ventas_inventario` (`id_venta`, `monto_total`, `costo_ventas`, `fecha`) VALUES
(1, 15000.00, 6000.00, '2026-10-03 16:57:00'),
(2, 8500.50, 3200.25, '2026-10-05 16:57:00'),
(3, 3000000.00, 2000000.00, '2026-10-21 16:05:25'),
(4, 750000.00, 5000000.00, '2026-10-21 16:06:34'),
(5, 50000.00, 20000.00, '2026-10-21 16:23:53');

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `aportes`
--
ALTER TABLE `aportes`
  ADD PRIMARY KEY (`id_aporte`);

--
-- Indices de la tabla `deducciones`
--
ALTER TABLE `deducciones`
  ADD PRIMARY KEY (`id_deduccion`);

--
-- Indices de la tabla `empleados`
--
ALTER TABLE `empleados`
  ADD PRIMARY KEY (`id_empleado`),
  ADD UNIQUE KEY `documento` (`documento`);

--
-- Indices de la tabla `etiquetas`
--
ALTER TABLE `etiquetas`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nombre` (`nombre`);

--
-- Indices de la tabla `gastos_deducibles`
--
ALTER TABLE `gastos_deducibles`
  ADD PRIMARY KEY (`id_gasto`),
  ADD KEY `fk_gastos_usuarios` (`id_usuario`);

--
-- Indices de la tabla `movimientos_inventario`
--
ALTER TABLE `movimientos_inventario`
  ADD PRIMARY KEY (`id_movimiento`),
  ADD KEY `idx_mov_producto` (`id_producto`),
  ADD KEY `idx_mov_fecha` (`fecha`);

--
-- Indices de la tabla `nomina`
--
ALTER TABLE `nomina`
  ADD PRIMARY KEY (`id_nomina`),
  ADD KEY `fk_nomina_empleado` (`id_empleado`);

--
-- Indices de la tabla `novedades`
--
ALTER TABLE `novedades`
  ADD PRIMARY KEY (`id_novedad`),
  ADD KEY `fk_novedad_empleado` (`id_empleado`);

--
-- Indices de la tabla `pagos_nomina`
--
ALTER TABLE `pagos_nomina`
  ADD PRIMARY KEY (`id_pago`);

--
-- Indices de la tabla `parametros`
--
ALTER TABLE `parametros`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nombre` (`nombre`),
  ADD KEY `etiqueta_id` (`etiqueta_id`);

--
-- Indices de la tabla `permisos`
--
ALTER TABLE `permisos`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nombre` (`nombre`);

--
-- Indices de la tabla `productos`
--
ALTER TABLE `productos`
  ADD PRIMARY KEY (`id_producto`),
  ADD UNIQUE KEY `codigo` (`codigo`);

--
-- Indices de la tabla `roles`
--
ALTER TABLE `roles`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nombre` (`nombre`);

--
-- Indices de la tabla `rol_permiso`
--
ALTER TABLE `rol_permiso`
  ADD PRIMARY KEY (`rol_id`,`permiso_id`),
  ADD KEY `permiso_id` (`permiso_id`);

--
-- Indices de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id_usuario`),
  ADD UNIQUE KEY `email` (`email`),
  ADD UNIQUE KEY `usuario` (`usuario`);

--
-- Indices de la tabla `ventas_inventario`
--
ALTER TABLE `ventas_inventario`
  ADD PRIMARY KEY (`id_venta`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `aportes`
--
ALTER TABLE `aportes`
  MODIFY `id_aporte` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `deducciones`
--
ALTER TABLE `deducciones`
  MODIFY `id_deduccion` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `empleados`
--
ALTER TABLE `empleados`
  MODIFY `id_empleado` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de la tabla `etiquetas`
--
ALTER TABLE `etiquetas`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `gastos_deducibles`
--
ALTER TABLE `gastos_deducibles`
  MODIFY `id_gasto` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `movimientos_inventario`
--
ALTER TABLE `movimientos_inventario`
  MODIFY `id_movimiento` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `nomina`
--
ALTER TABLE `nomina`
  MODIFY `id_nomina` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `novedades`
--
ALTER TABLE `novedades`
  MODIFY `id_novedad` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `pagos_nomina`
--
ALTER TABLE `pagos_nomina`
  MODIFY `id_pago` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `parametros`
--
ALTER TABLE `parametros`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `permisos`
--
ALTER TABLE `permisos`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT de la tabla `productos`
--
ALTER TABLE `productos`
  MODIFY `id_producto` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `roles`
--
ALTER TABLE `roles`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `id_usuario` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT de la tabla `ventas_inventario`
--
ALTER TABLE `ventas_inventario`
  MODIFY `id_venta` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `gastos_deducibles`
--
ALTER TABLE `gastos_deducibles`
  ADD CONSTRAINT `fk_gastos_usuarios` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON UPDATE CASCADE;

--
-- Filtros para la tabla `movimientos_inventario`
--
ALTER TABLE `movimientos_inventario`
  ADD CONSTRAINT `fk_mov_producto` FOREIGN KEY (`id_producto`) REFERENCES `productos` (`id_producto`);

--
-- Filtros para la tabla `nomina`
--
ALTER TABLE `nomina`
  ADD CONSTRAINT `fk_nomina_empleado` FOREIGN KEY (`id_empleado`) REFERENCES `empleados` (`id_empleado`);

--
-- Filtros para la tabla `novedades`
--
ALTER TABLE `novedades`
  ADD CONSTRAINT `fk_novedad_empleado` FOREIGN KEY (`id_empleado`) REFERENCES `empleados` (`id_empleado`);

--
-- Filtros para la tabla `parametros`
--
ALTER TABLE `parametros`
  ADD CONSTRAINT `parametros_ibfk_1` FOREIGN KEY (`etiqueta_id`) REFERENCES `etiquetas` (`id`) ON DELETE CASCADE;

--
-- Filtros para la tabla `rol_permiso`
--
ALTER TABLE `rol_permiso`
  ADD CONSTRAINT `rol_permiso_ibfk_1` FOREIGN KEY (`rol_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `rol_permiso_ibfk_2` FOREIGN KEY (`permiso_id`) REFERENCES `permisos` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

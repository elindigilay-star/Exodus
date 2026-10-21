-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 09-10-2026 a las 00:09:35
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `sistema_contable`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `gastos_deducibles`
--

CREATE TABLE `gastos_deducibles` (
  `id_gasto` int(11) NOT NULL,
  `descripcion` varchar(255) NOT NULL,
  `monto` decimal(12,2) NOT NULL,
  `fecha` datetime NOT NULL DEFAULT current_timestamp(),
  `id_usuario` int(11) NOT NULL
) ;

--
-- Volcado de datos para la tabla `gastos_deducibles`
--

INSERT INTO `gastos_deducibles` (`id_gasto`, `descripcion`, `monto`, `fecha`, `id_usuario`) VALUES
(1, 'Gasto de oficina', 250.00, '2026-10-07 16:57:00', 1),
(2, 'Servicios públicos', 180.50, '2026-09-28 16:57:00', 1);

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
-- Estructura de tabla para la tabla `usuarios`
--

CREATE TABLE `usuarios` (
  `id_usuario` int(11) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `rol` enum('Administrador','Contador','Auxiliar','Empleado') NOT NULL DEFAULT 'Empleado'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `usuarios`
--

INSERT INTO `usuarios` (`id_usuario`, `nombre`, `email`, `rol`) VALUES
(1, 'Carlos Pérez', 'carlos@empresa.com', 'Administrador'),
(2, 'Ana Gómez', 'ana@empresa.com', 'Contador'),
(3, 'Juan Torres', 'juan@empresa.com', 'Auxiliar'),
(4, 'Administrador Principal', 'admin@sistema.com', 'Administrador'),
(5, 'Contador Jefe', 'contador@sistema.com', 'Contador'),
(6, 'Auxiliar Administrativo', 'auxiliar@sistema.com', 'Auxiliar');

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
(2, 8500.50, 3200.25, '2026-10-05 16:57:00');

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `gastos_deducibles`
--
ALTER TABLE `gastos_deducibles`
  ADD PRIMARY KEY (`id_gasto`),
  ADD KEY `fk_gastos_usuarios` (`id_usuario`);

--
-- Indices de la tabla `pagos_nomina`
--
ALTER TABLE `pagos_nomina`
  ADD PRIMARY KEY (`id_pago`);

--
-- Indices de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  ADD PRIMARY KEY (`id_usuario`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indices de la tabla `ventas_inventario`
--
ALTER TABLE `ventas_inventario`
  ADD PRIMARY KEY (`id_venta`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `gastos_deducibles`
--
ALTER TABLE `gastos_deducibles`
  MODIFY `id_gasto` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `pagos_nomina`
--
ALTER TABLE `pagos_nomina`
  MODIFY `id_pago` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `usuarios`
--
ALTER TABLE `usuarios`
  MODIFY `id_usuario` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT de la tabla `ventas_inventario`
--
ALTER TABLE `ventas_inventario`
  MODIFY `id_venta` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `gastos_deducibles`
--
ALTER TABLE `gastos_deducibles`
  ADD CONSTRAINT `fk_gastos_usuarios` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON UPDATE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;

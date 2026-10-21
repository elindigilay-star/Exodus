-- =========================================================
-- EXODUS Contable - Módulo de Nómina (RF-6, RF-7, RF-8, RF-9)
-- Importa este archivo completo desde phpMyAdmin (pestaña "Importar")
-- =========================================================

CREATE DATABASE IF NOT EXISTS exodus_nomina
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE exodus_nomina;

-- ---------------------------------------------------------
-- RF-6 / RF-7: empleados
-- estado ACTIVO/INACTIVO en vez de borrar la fila:
-- si se hiciera DELETE real, se perdería el historial de
-- nómina y de novedades del empleado (y las llaves foráneas
-- de abajo lo impedirían). "Eliminar" en RF-7 = marcar INACTIVO.
-- ---------------------------------------------------------
CREATE TABLE empleados (
    id_empleado    INT AUTO_INCREMENT PRIMARY KEY,
    nombres        VARCHAR(100) NOT NULL,
    apellidos      VARCHAR(100) NOT NULL,
    documento      VARCHAR(30)  NOT NULL UNIQUE,
    cargo          VARCHAR(100),
    salario_base   DECIMAL(12,2) NOT NULL,
    fecha_ingreso  DATE NOT NULL,
    estado         ENUM('ACTIVO','INACTIVO') NOT NULL DEFAULT 'ACTIVO',
    creado_en      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------
-- RF-8: configuración de deducciones (le restan al empleado)
-- y aportes (los paga la empresa, no restan el neto del empleado,
-- pero el reporte los muestra como costo de nómina)
-- ---------------------------------------------------------
CREATE TABLE deducciones (
    id_deduccion   INT AUTO_INCREMENT PRIMARY KEY,
    nombre         VARCHAR(100) NOT NULL,
    porcentaje     DECIMAL(6,3) NOT NULL,
    activo         TINYINT(1)   NOT NULL DEFAULT 1
);

CREATE TABLE aportes (
    id_aporte      INT AUTO_INCREMENT PRIMARY KEY,
    nombre         VARCHAR(100) NOT NULL,
    porcentaje     DECIMAL(6,3) NOT NULL,
    activo         TINYINT(1)   NOT NULL DEFAULT 1
);

-- Reporte generado cada vez que se calcula la nómina de un empleado/periodo
CREATE TABLE nomina (
    id_nomina           INT AUTO_INCREMENT PRIMARY KEY,
    id_empleado         INT NOT NULL,
    periodo             VARCHAR(7) NOT NULL, -- formato 'YYYY-MM'
    salario_base        DECIMAL(12,2) NOT NULL,
    total_deducciones   DECIMAL(12,2) NOT NULL,
    total_aportes       DECIMAL(12,2) NOT NULL,
    salario_neto        DECIMAL(12,2) NOT NULL,
    generado_en         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_nomina_empleado FOREIGN KEY (id_empleado)
        REFERENCES empleados(id_empleado)
);

-- ---------------------------------------------------------
-- RF-9: ausencias, vacaciones y permisos
-- ---------------------------------------------------------
CREATE TABLE novedades (
    id_novedad     INT AUTO_INCREMENT PRIMARY KEY,
    id_empleado    INT NOT NULL,
    tipo           ENUM('AUSENCIA','VACACIONES','PERMISO') NOT NULL,
    fecha_inicio   DATE NOT NULL,
    fecha_fin      DATE NOT NULL,
    motivo         VARCHAR(255),
    estado         ENUM('PENDIENTE','APROBADA','RECHAZADA') NOT NULL DEFAULT 'PENDIENTE',
    creado_en      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_novedad_empleado FOREIGN KEY (id_empleado)
        REFERENCES empleados(id_empleado)
);

-- ---------------------------------------------------------
-- Datos semilla para poder probar el cálculo de nómina (RF-8)
-- sin tener que crearlos manualmente antes. Ajusta los nombres
-- y porcentajes a lo que pida tu docente/normativa.
-- ---------------------------------------------------------
INSERT INTO deducciones (nombre, porcentaje) VALUES
    ('Salud (empleado)', 4.000),
    ('Pensión (empleado)', 4.000);

INSERT INTO aportes (nombre, porcentaje) VALUES
    ('Salud (empleador)', 8.500),
    ('Pensión (empleador)', 12.000),
    ('ARL', 0.522);

-- Un empleado de ejemplo para que puedas probar de una vez
INSERT INTO empleados (nombres, apellidos, documento, cargo, salario_base, fecha_ingreso, estado) VALUES
    ('Laura', 'Gómez', '1001234567', 'Auxiliar contable', 1800000.00, '2025-03-01', 'ACTIVO');

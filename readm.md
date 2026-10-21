# ESPECIFICACIÓN DE REQUISITOS DE SOFTWARE

**PROYECTO:** Desarrollo de un software integral para la administración, gestión y contabilidad de las PYMES (Pequeñas y Medianas Empresas) — **EXODUS CONTABLE**

*(Avances – V3)*

**Presentado por:**

- Andrés Camilo Sarmiento Leudo
- Nicolás Fermín Berrio Teherán
- Camilo Andrés Meza de Ávila

**ANALISIS Y DESARROLLO DE SOFTWARE** — FICHA: 3315527

SERVICIO NACIONAL DE APRENDIZAJE – SENA

2026

---

## TABLA DE CONTENIDO

- [Introducción](#introducción)
- [1. Planteamiento del problema](#1-planteamiento-del-problema)
  - [1.1 Descripción del Problema](#11-descripción-del-problema)
  - [1.2 Formulación del Problema](#12-formulación-del-problema)
- [2. Objetivos](#2-objetivos)
  - [2.1 Objetivo General](#21-objetivo-general)
  - [2.2 Objetivos Específicos](#22-objetivos-específicos)
- [3. Requisitos del Sistema](#3-requisitos-del-sistema)
  - [3.1 Requisitos Funcionales](#31-requisitos-funcionales)
  - [3.2 Requisitos No Funcionales](#32-requisitos-no-funcionales)
- [4. Justificación](#4-justificación)
- [5. Mapa de Procesos](#5-mapa-de-procesos)
- [6. Metodología](#6-metodología)
- [7. Diagrama de Casos de Uso](#7-diagrama-de-casos-de-uso)
  - [7.1 Descripción de Casos de Uso](#71-descripción-de-casos-de-uso)
- [8. Diagramas UML](#8-diagramas-uml)
- [9. Diagrama de Gantt](#9-diagrama-de-gantt)
- [10. Conclusión](#10-conclusión)

---

## Introducción

Actualmente, muchas PYMES en Colombia tienen problemas para organizar sus procesos contables, de inventario y nómina, ya que suelen trabajar con registros manuales o herramientas separadas como hojas de cálculo o archivos independientes. Esto provoca errores, pérdida de información y falta de control, además de dificultades para integrar los datos entre las diferentes áreas de la empresa. También se presentan retos en el cumplimiento de normas legales y en el acceso a software contable, debido a los altos costos o requerimientos técnicos.

Por esta razón, nace **Exodus Contable**, un software de escritorio que busca facilitar la gestión empresarial mediante la integración de los módulos de inventario, nómina y contabilidad en un solo sistema. La idea es ofrecer una herramienta práctica, accesible y fácil de usar, que funcione sin necesidad de internet y ayude a las empresas a llevar un control más claro, seguro y automatizado de su información financiera.

---

## 1. Planteamiento del problema

Las pequeñas y medianas empresas (PYMES) en Colombia presentan dificultades en la gestión de sus procesos contables, administrativos y de inventario debido al uso de métodos manuales o herramientas no integradas. Esta situación genera desorganización en la información, errores frecuentes y una baja eficiencia en la administración de los recursos, afectando directamente la toma de decisiones y el control financiero de las empresas.

### 1.1 Descripción del problema

En muchas PYMES, los procesos de inventario, nómina y contabilidad se manejan de forma independiente, utilizando hojas de cálculo, cuadernos o archivos digitales separados. Esto provoca inconsistencias en la información, duplicidad de datos y falta de sincronización entre áreas. Además, los cálculos de nómina y reportes financieros suelen realizarse manualmente, lo que aumenta el riesgo de errores y el incumplimiento de la normativa legal colombiana.

Por otro lado, el acceso a software contable especializado es limitado debido a sus altos costos o a la necesidad de infraestructura tecnológica avanzada. Asimismo, la falta de un sistema centralizado incrementa el riesgo de pérdida de información y dificulta el control y la seguridad de los datos empresariales.

### 1.2 Formulación del problema

¿Cómo desarrollar un sistema de software de escritorio, accesible e integrado, que permita a las PYMES gestionar de manera eficiente sus procesos de inventario, nómina y contabilidad, garantizando la organización, confiabilidad y cumplimiento normativo de la información?

---

## 2. Objetivos

### 2.1 Objetivo General

Desarrollar un software de escritorio que permita a las PYMES gestionar de manera integrada los procesos de inventario, nómina y contabilidad, mejorando la organización, el control y la confiabilidad de la información financiera.

### 2.2 Objetivos Específicos

- **OB-01** Controlar el acceso al sistema mediante autenticación de usuarios y gestión de roles y permisos.
- **OB-02** Facilitar el acceso al sistema mediante funciones de recordatorio de usuario.
- **OB-03** Administrar los usuarios del sistema, incluyendo su creación, edición y eliminación.
- **OB-04** Gestionar la configuración general del sistema.
- **OB-05** Permitir la parametrización de procesos contables mediante etiquetas y clasificación de productos.
- **OB-06** Garantizar la adaptación del sistema a la normativa legal vigente.
- **OB-07** Gestionar el inventario de productos, incluyendo su registro, actualización y control.
- **OB-08** Clasificar y organizar los productos dentro del sistema.
- **OB-09** Controlar los niveles de stock mediante el registro de entradas y salidas.
- **OB-10** Facilitar la consulta y visualización de la información del inventario.
- **OB-11** Gestionar la información de los empleados.
- **OB-12** Calcular automáticamente la nómina, incluyendo deducciones y aportes.
- **OB-13** Registrar y gestionar novedades laborales de los empleados.
- **OB-14** Registrar y consolidar la información contable del sistema.
- **OB-15** Generar reportes financieros y estados contables.

---

## 3. Requisitos Del Software

### 3.1 Requisitos Funcionales

| Código | Requisito Funcional | Descripción | Objetivos Asociados |
| --- | --- | --- | --- |
| **Módulo de Inventario** | | | |
| RF-01 | Registrar productos | Permite registrar productos con código, nombre, tipo y precios | OB-07, OB-08 |
| RF-02 | Registrar entradas de inventario | Permite aumentar el stock de productos existentes | OB-07, OB-09 |
| RF-03 | Registrar salidas de inventario | Permite disminuir el stock y afectar contabilidad | OB-07, OB-09 |
| RF-04 | Clasificar productos | El usuario asigna el tipo de producto para cálculos contables | OB-08, OB-05 |
| RF-05 | Administración integral de productos | Permite consultar, eliminar o actualizar los productos. | OB-07, OB-10 |
| **Módulo de Nómina** | | | |
| RF-06 | Registrar empleados | Permite ingresar empleados con datos laborales | OB-11 |
| RF-07 | Eliminar empleados | Permite eliminar empleados del sistema | OB-11 |
| RF-08 | Calcular nómina | Calcula salario neto con deducciones y aportes | OB-12, OB-06 |
| RF-09 | Registrar novedades laborales | Permite registrar permisos, ausencias y vacaciones | OB-13 |
| **Módulo de Contabilidad** | | | |
| RF-10 | Generar estado de resultados | Consolida datos financieros del sistema | OB-15, OB-14 |
| RF-11 | Registrar gastos deducibles | Permite registrar egresos manuales | OB-14 |
| RF-12 | Consolidar información contable | Integra los datos de inventario y de nómina | OB-14, OB-15 |
| RF-13 | Calcular balance general | Calcula activos, pasivos y patrimonio, y estado de resultados | OB-15 |
| RF-14 | Generar reportes contables | Genera y exporta reportes financieros | OB-14, OB-15 |
| **Módulo de Configuración** | | | |
| RF-15 | Gestionar etiquetas | Permite crear, editar y eliminar etiquetas | OB-04, OB-05 |
| RF-16 | Ajustar parámetros | Permite modificar valores legales y contables a través de etiquetas. | OB-04, OB-06 |
| RF-17 | Gestionar usuarios | Permite crear, editar y eliminar usuarios | OB-03 |
| RF-18 | Gestionar roles y permisos | Permite controlar accesos por rol | OB-01, OB-03 |
| **Módulo de Seguridad** | | | |
| RF-19 | Iniciar sesión | Permite autenticación de usuarios | OB-01 |
| RF-20 | Recordar usuario | Permite guardar credenciales de acceso | OB-02 |

### 3.2 Requisitos No Funcionales

| Código | Categoría | Requisito No Funcional | Descripción |
| --- | --- | --- | --- |
| RNF-01 | Seguridad | Autenticación de usuarios | El sistema debe requerir credenciales válidas para el acceso |
| RNF-02 | Seguridad | Control de acceso por roles | El sistema debe restringir funcionalidades según el rol del usuario |
| RNF-03 | Seguridad | Protección de datos | La información de usuarios debe almacenarse de forma segura |
| RNF-04 | Rendimiento | Tiempo de respuesta | El sistema debe responder a las acciones del usuario en menos de 2 segundos |
| RNF-05 | Rendimiento | Eficiencia en cálculos | Los cálculos deben ejecutarse de forma rápida y precisa |
| RNF-06 | Usabilidad | Interfaz amigable | El sistema debe ser intuitivo y fácil de usar |
| RNF-07 | Usabilidad | Navegación clara | El sistema debe permitir una navegación sencilla entre módulos |
| RNF-08 | Usabilidad | Recordatorio de usuario | El sistema debe facilitar el acceso mediante almacenamiento de credenciales |
| RNF-09 | Mantenibilidad | Código modular | El sistema debe estar estructurado en módulos independientes |
| RNF-10 | Mantenibilidad | Facilidad de actualización | Debe permitir cambios sin afectar otros módulos |
| RNF-11 | Disponibilidad | Disponibilidad del sistema | El sistema debe estar disponible durante el horario laboral |
| RNF-12 | Disponibilidad | Manejo de errores | El sistema debe gestionar errores sin pérdida de información |
| RNF-13 | Escalabilidad | Crecimiento del sistema | Debe permitir la incorporación de nuevos módulos |
| RNF-14 | Escalabilidad | Manejo de datos | Debe soportar incremento en volumen de información |
| RNF-15 | Legalidad | Cumplimiento normativo | Debe cumplir con la normativa legal vigente |
| RNF-16 | Legalidad | Actualización legal | Debe permitir modificar parámetros legales fácilmente |

---

## 4. Justificación

El desarrollo de Exodus Contable se justifica por la necesidad que tienen las pequeñas y medianas empresas (PYMES) de contar con una herramienta que les permita gestionar de manera organizada sus procesos contables, de inventario y nómina. Actualmente, muchas de estas empresas utilizan métodos manuales o sistemas no integrados, lo que genera errores, pérdida de información y dificultades en el control de sus operaciones financieras.

Además, la implementación de este software representa una alternativa accesible frente a los sistemas contables tradicionales, que suelen ser costosos o requieren infraestructura tecnológica avanzada. Exodus Contable busca ofrecer una solución práctica, de fácil uso y sin necesidad de conexión a internet, permitiendo a las empresas mejorar su eficiencia operativa y optimizar la toma de decisiones.

Finalmente, este sistema contribuye al cumplimiento de la normativa contable y laboral colombiana, automatizando procesos clave como el cálculo de nómina y la generación de reportes financieros. De esta manera, no solo se mejora la organización interna de las empresas, sino que también se reduce el riesgo de errores y sanciones legales, fortaleciendo su crecimiento y sostenibilidad.

---

## 5. Mapa de Procesos

> _(Espacio reservado para el mapa de procesos)_

---

## 6. Metodología

Para el desarrollo del proyecto Exodus Contable se utilizará una metodología de tipo incremental, la cual permite construir el sistema por módulos funcionales, facilitando su desarrollo, prueba y mejora continua. Esta metodología es adecuada debido a la estructura modular del sistema (inventario, nómina, contabilidad, configuración y seguridad), permitiendo avanzar de manera organizada y controlada en cada componente.

El proceso inicia con la fase de análisis de requisitos, donde se identifican las necesidades del sistema y se definen los requerimientos funcionales y no funcionales. Posteriormente, se realiza el diseño del sistema, incluyendo la estructura de los módulos, la interfaz gráfica y la organización de los datos. Luego, se lleva a cabo la implementación utilizando el lenguaje de programación **Python** y librerías como **Tkinter**, seguido de pruebas por cada módulo para verificar su correcto funcionamiento.

Finalmente, se realiza la integración de todos los módulos en un solo sistema, junto con pruebas generales y ajustes necesarios. Esta metodología permite detectar errores de manera temprana, mejorar progresivamente el software y asegurar que el producto final cumpla con los objetivos planteados.

---

## 7. Diagrama de Casos de Uso

> _(Espacio reservado para el diagrama de casos de uso)_

### 7.1 Descripción de Casos de Uso

Los requisitos asociados fueron redefinidos como requisitos de información (RI) para asegurar la trazabilidad técnica entre los procesos contables y los objetivos del sistema.

#### RF-01 — Registrar Producto

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Nicolás Fermín Berrio Teherán |
| **Objetivos asociados** | OB-07 Gestión de inventario; OB-08 Control de productos |
| **Requisitos asociados** | RI-09 Registro de productos; RI-10 Clasificación de productos |
| **Descripción** | El sistema permitirá al usuario registrar nuevos productos en el inventario, definiendo sus características como nombre, código, tipo, precio base y precio de venta. |
| **Precondición** | El usuario debe haber iniciado sesión y tener acceso al módulo de inventario. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El usuario accede al módulo de inventario |
| 2 | El sistema muestra las opciones disponibles |
| 3 | El usuario selecciona "Agregar producto" |
| 4 | El sistema muestra el formulario de registro |
| 5 | El usuario ingresa los datos del producto |
| 6 | El usuario confirma el registro |
| 7 | El sistema valida los datos |
| 8 | El sistema guarda el producto |
| 9 | El sistema muestra confirmación |

**Excepción**

| Paso | Acción |
| --- | --- |
| 7 | Si hay campos vacíos, el sistema solicita completar |
| 7 | Si el código ya existe, el sistema muestra error |

| Campo | Valor |
| --- | --- |
| **Postcondición** | El producto queda registrado en el sistema. |
| **Importancia** | Alta |
| **Urgencia** | Inmediata |
| **Comentarios** | Ninguno. |

#### RF-02 — Registrar Entrada de Inventario

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Nicolás Fermín Berrio Teherán |
| **Objetivos asociados** | OB-07 Gestión de inventario; OB-09 Control de stock |
| **Requisitos asociados** | RI-11 Registro de movimientos de inventario |
| **Descripción** | Permite registrar el ingreso de productos al inventario, aumentando su cantidad disponible. |
| **Precondición** | El producto debe existir. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El usuario selecciona un producto |
| 2 | Selecciona "Entrada de inventario" |
| 3 | Ingresa cantidad |
| 4 | Confirma operación |
| 5 | El sistema actualiza el stock |

**Excepción**

| Paso | Acción |
| --- | --- |
| 3 | Si la cantidad es inválida, el sistema muestra error |

| Campo | Valor |
| --- | --- |
| **Postcondición** | El stock del producto aumenta. |
| **Importancia** | Alta |
| **Urgencia** | Importante. |
| **Comentarios** | Ninguno. |

#### RF-03 — Registrar Salida de Inventario

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Nicolás Fermín Berrio Teherán |
| **Objetivos asociados** | OB-07 Gestión de inventario; OB-09 Control de stock |
| **Requisitos asociados** | RI-11 Registro de movimientos de inventario |
| **Descripción** | Permite registrar la salida de productos del inventario. |
| **Precondición** | Debe existir stock suficiente. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El usuario selecciona un producto |
| 2 | Selecciona "Salida de inventario" |
| 3 | Ingresa cantidad |
| 4 | Confirma operación |
| 5 | El sistema descuenta el stock |

**Excepción**

| Paso | Acción |
| --- | --- |
| 3 | Si no hay stock suficiente, el sistema muestra error |

| Campo | Valor |
| --- | --- |
| **Postcondición** | El stock del producto disminuye. |
| **Importancia** | Alta |
| **Urgencia** | Importante. |
| **Comentarios** | Ninguno. |

#### RF-04 — Clasificar Productos

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Nicolás Fermín Berrio Teherán |
| **Objetivos asociados** | OB-08 Control de productos; OB-05 Permitir la parametrización de procesos contables |
| **Requisitos asociados** | RI-10 Clasificación de productos |
| **Descripción** | El sistema permitirá al usuario asignar o modificar la clasificación de los productos, definiendo su tipo o categoría con el fin de facilitar su organización y su uso en procesos contables. |
| **Precondición** | El usuario debe haber iniciado sesión y el producto debe estar previamente registrado. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El usuario accede al módulo de inventario |
| 2 | El sistema muestra la lista de productos registrados |
| 3 | El usuario selecciona un producto |
| 4 | El usuario selecciona la opción "Clasificar producto" |
| 5 | El sistema muestra las categorías o tipos disponibles |
| 6 | El usuario selecciona o asigna una categoría al producto |
| 7 | El usuario confirma la operación |
| 8 | El sistema valida la información |
| 9 | El sistema guarda la clasificación del producto |
| 10 | El sistema muestra un mensaje de confirmación |

**Excepción**

| Paso | Acción |
| --- | --- |
| 8 | Si no se selecciona ninguna categoría, el sistema solicita completar la información |
| 8 | Si ocurre un error en la asignación, el sistema muestra un mensaje de error |

| Campo | Valor |
| --- | --- |
| **Postcondición** | El producto queda clasificado dentro del sistema y listo para su uso en procesos contables. |
| **Importancia** | Alta |
| **Urgencia** | Importante. |
| **Comentarios** | La clasificación de productos es fundamental para la correcta aplicación de cálculos contables y organización del inventario. |

#### RF-05 — Actualizar Producto

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Nicolás Fermín Berrio Teherán |
| **Objetivos asociados** | OB-07 Gestión de inventario |
| **Requisitos asociados** | RI-09 Registro de productos |
| **Descripción** | Permite modificar la información de un producto existente. |
| **Precondición** | El producto debe existir. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El usuario selecciona un producto |
| 2 | Modifica los datos |
| 3 | Confirma cambios |
| 4 | El sistema actualiza la información |

**Excepción**

| Paso | Acción |
| --- | --- |
| 3 | Si hay datos inválidos, el sistema muestra error |

| Campo | Valor |
| --- | --- |
| **Postcondición** | El producto queda actualizado. |
| **Importancia** | Alta |
| **Urgencia** | Media |
| **Comentarios** | Ninguno. |

#### RF-05 — Eliminar Producto

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Nicolás Fermín Berrio Teherán |
| **Objetivos asociados** | OB-07 Gestión de inventario |
| **Requisitos asociados** | RI-09 Registro de productos |
| **Descripción** | Permite eliminar un producto del sistema. |
| **Precondición** | El producto debe existir. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El usuario selecciona un producto |
| 2 | Confirma eliminación |
| 3 | El sistema elimina el producto |

**Excepción**

| Paso | Acción |
| --- | --- |
| 2 | Si cancela, no se elimina |
| 3 | Si el producto tiene movimientos, el sistema impide eliminarlo |

| Campo | Valor |
| --- | --- |
| **Postcondición** | El producto queda eliminado del sistema. |
| **Importancia** | Alta |
| **Urgencia** | Intermedia |
| **Comentarios** | Ninguno. |

#### RF-05 — Consultar Inventario

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Nicolás Fermín Berrio Teherán |
| **Objetivos asociados** | OB-07 Gestión de inventario; OB-10 Visualización de información |
| **Requisitos asociados** | RI-12 Consulta de productos |
| **Descripción** | Permite visualizar los productos registrados y su estado en el inventario. |
| **Precondición** | El usuario debe tener acceso al módulo. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El usuario accede al módulo |
| 2 | El sistema muestra la lista de productos |
| 3 | El usuario consulta información |

**Excepción**

| Paso | Acción |
| --- | --- |
| No Aplica | No aplica |

| Campo | Valor |
| --- | --- |
| **Postcondición** | El usuario visualiza el estado del inventario. |
| **Importancia** | Alta |
| **Urgencia** | Media |
| **Comentarios** | Ninguno. |

#### RF-06 — Registrar Empleados

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Andrés Camilo Sarmiento Leudo |
| **Objetivos asociados** | OB-11 Gestionar la información de los empleados. |
| **Requisitos asociados** | RI-13 Registro de información de empleados; RI-14 Validación de datos de empleados |
| **Descripción** | El sistema deberá permitir al administrador registrar nuevos empleados en la aplicación. |
| **Precondición** | El administrador debe tener acceso habilitado y el empleado no debe estar previamente registrado. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El administrador selecciona "Registrar Empleados" |
| 2 | El sistema solicita datos del empleado |
| 3 | El sistema valida la información |
| 4 | Si es correcta, guarda el registro |
| 5 | Asigna estado ACTIVO |

**Excepción**

| Paso | Acción |
| --- | --- |
| 5 | Si los datos del empleado son incompletos, el sistema muestra mensaje y solicita corrección |
| 5 | Si el empleado ya existe en el sistema, se muestra mensaje de error y se detiene el registro |
| 5 | Si el administrador no tiene permisos, el sistema muestra mensaje de acceso denegado |

| Campo | Valor |
| --- | --- |
| **Postcondición** | El empleado queda registrado y activo en el sistema. |
| **Importancia** | Vital |
| **Urgencia** | Inmediata |
| **Comentarios** | Este caso de uso pertenece al módulo de Nómina y se conecta con el actor RRHH. En el diagrama general de EXODUS Contable se muestra como parte de las funciones de Recursos Humanos. El área de RRHH ingresa los datos del nuevo empleado, el sistema valida la información y, si es correcta, guarda el registro y lo marca como activo. |

#### RF-07 — Eliminar Empleados

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Andrés Camilo Sarmiento Leudo |
| **Objetivos asociados** | OB-11 Gestionar la información de los empleados |
| **Requisitos asociados** | RI-13 Gestión de información de empleados; RI-15 Eliminación de empleados |
| **Descripción** | El sistema deberá permitir al administrador eliminar empleados registrados en la aplicación, manteniendo la integridad de la base de datos. |
| **Precondición** | El empleado debe estar registrado en el sistema y el administrador debe tener permisos para realizar la acción. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El administrador selecciona la opción "Eliminar Empleado". |
| 2 | El sistema solicita el identificador del empleado. |
| 3 | El sistema valida que el empleado exista. |
| 4 | El sistema solicita confirmación de la acción. |
| 5 | Si se confirma, el sistema elimina el registro del empleado. |
| 6 | El sistema actualiza la base de datos y muestra mensaje de éxito. |

**Excepción**

| Paso | Acción |
| --- | --- |
| 3 | Si el empleado no existe, el sistema muestra mensaje de error y detiene el proceso. |
| 4 | Si el administrador cancela la acción, el sistema no elimina el registro y regresa al menú principal. |
| 5 | Si el administrador no tiene permisos, el sistema muestra mensaje de acceso denegado. |

| Campo | Valor |
| --- | --- |
| **Postcondición** | El empleado queda eliminado del sistema y no puede acceder a la aplicación. |
| **Importancia** | Alta |
| **Urgencia** | Inmediata |
| **Comentarios** | Este caso de uso pertenece al módulo de Nómina y se conecta con el actor RRHH. En el diagrama general de EXODUS Contable se muestra como parte de las funciones de Recursos Humanos. El área de RRHH selecciona la opción de eliminar empleado, el sistema valida que el registro exista y que el administrador tenga permisos. Si la información es correcta y se confirma la acción, el sistema elimina el registro y actualiza la base de datos, marcando al empleado como inactivo o eliminado. |

#### RF-08 — Calcular Salario Neto con Deducciones y Aportes

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Andrés Camilo Sarmiento Leudo |
| **Objetivos asociados** | OB-12 Calcular automáticamente la nómina; OB-06 Garantizar la adaptación a la normativa legal vigente |
| **Requisitos asociados** | RI-16 Cálculo de salario neto; RI-17 Aplicación de deducciones; RI-18 Aplicación de aportes; RI-19 Generación de reportes de nómina |
| **Descripción** | El sistema deberá calcular el salario neto aplicando deducciones y aportes configurados en la nómina. |
| **Precondición** | El empleado debe estar registrado y contar con salario base definido. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El administrador selecciona la opción "Calcular Salario Neto" |
| 2 | El sistema solicita los datos del empleado. |
| 3 | El sistema aplica deducciones configuradas. |
| 4 | El sistema aplica aportes correspondientes. |
| 5 | El sistema calcula el salario neto. |
| 6 | El sistema genera y muestra el reporte. |

**Excepción**

| Paso | Acción |
| --- | --- |
| 2 | Si faltan datos del empleado, el sistema muestra mensaje y solicita corrección. |
| 3 | Si no existe configuración de deducciones, el sistema muestra error y detiene el cálculo. |
| 4 | Si ocurre error en el cálculo de aportes, el sistema muestra mensaje y reinicia proceso. |

| Campo | Valor |
| --- | --- |
| **Postcondición** | Se genera reporte con el salario neto calculado, incluyendo deducciones y aportes aplicados. |
| **Importancia** | Vital |
| **Urgencia** | Inmediata |
| **Comentarios** | Este caso de uso pertenece al módulo de Nómina y se conecta con el actor RRHH. En el diagrama general de EXODUS Contable se muestra como parte de las funciones de Recursos Humanos. El área de RRHH solicita el cálculo del salario neto, el sistema aplica las deducciones y aportes configurados, y finalmente genera el reporte con el resultado. |

#### RF-09 — Gestionar Ausencias, Vacaciones y Permisos

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Andrés Camilo Sarmiento Leudo |
| **Objetivos asociados** | OB-13 |
| **Requisitos asociados** | RF-09 Registrar novedades laborales |
| **Descripción** | El sistema deberá permitir a los empleados registrar solicitudes de ausencia, vacaciones o permisos, y al administrador validarlas y aprobarlas. |
| **Precondición** | El empleado debe estar registrado y tener acceso habilitado. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El empleado registra solicitud |
| 2 | El sistema valida disponibilidad |
| 3 | El administrador aprueba o rechaza |
| 4 | El sistema actualiza estado |
| 5 | El sistema notifica resultado |

**Excepción**

| Paso | Acción |
| --- | --- |
| 2 | Si la solicitud está incompleta, el sistema muestra mensaje y solicita corrección |
| 3 | Si el administrador no responde, el sistema deja solicitud en estado pendiente |
| 2 | Si no hay disponibilidad, el sistema muestra mensaje y rechaza solicitud |

| Campo | Valor |
| --- | --- |
| **Postcondición** | La solicitud queda registrada con estado actualizado y notificación enviada. |
| **Importancia** | Alta |
| **Urgencia** | Inmediata |
| **Comentarios** | Este caso de uso pertenece al módulo de Nómina y se conecta con el actor RRHH. En el diagrama general se muestra como parte de las funciones de Recursos Humanos, relacionadas con la gestión de solicitudes de empleados. El empleado registra una solicitud de ausencia, vacaciones o permisos; el sistema valida la disponibilidad; el administrador aprueba o rechaza la solicitud; y finalmente el sistema actualiza el estado y notifica el resultado. |

#### RF-10 — Generar Estado de Resultados

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Camilo Andrés Meza De Ávila |
| **Objetivos asociados** | OB-15 Generar reportes financieros y estados contables; OB-14 Registrar y consolidar la información contable del sistema |
| **Requisitos asociados** | RI-23 Generación de estado de resultados; RI-24 Integración de datos de inventario; RI-25 Integración de datos de nómina; RI-26 Cálculo de ingresos, egresos y utilidades |
| **Descripción** | Consolida datos financieros del sistema. |
| **Precondición** | Existen datos registrados en inventario y nómina. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El usuario solicita generar el estado de resultados |
| 2 | El sistema recopila información de inventario |
| 3 | El sistema recopila información de nómina |
| 4 | El sistema calcula ingresos, egresos y utilidades |
| 5 | El sistema muestra el estado de resultados |

**Excepción**

| Paso | Acción |
| --- | --- |
| 3 | Si no hay datos suficientes, el sistema muestra mensajes de error |

| Campo | Valor |
| --- | --- |
| **Postcondición** | Se genera y muestra el estado de resultados. |
| **Importancia** | Vital |
| **Urgencia** | Inmediata |
| **Comentarios** | Este caso de uso se asocia con el proceso Generar estado de resultados dentro del diagrama, el cual es ejecutado por el actor Contador. Su funcionamiento depende de información proveniente de otros procesos como Registrar gastos, Entrada y salida de inventario y Calcular nómina, ya que estos suministran los datos necesarios. |

#### RF-11 — Registrar Gastos Deducibles

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Camilo Andrés Meza De Ávila |
| **Objetivos asociados** | OB-14 Registrar y consolidar la información contable del sistema |
| **Requisitos asociados** | RI-27 Registro de gastos contables; RI-28 Validación de datos financieros |
| **Descripción** | Permite registrar egresos manuales. |
| **Precondición** | Usuario con permisos (Contador o Administrador). |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El usuario accede a la opción de registrar gasto |
| 2 | El sistema solicita la descripción y el monto |
| 3 | El usuario ingresa los datos |
| 4 | El sistema valida la información |
| 5 | El sistema guarda el gasto |

**Excepción**

| Paso | Acción |
| --- | --- |
| 4 | Si los datos están vacíos o incorrectos, el sistema muestra error |

| Campo | Valor |
| --- | --- |
| **Postcondición** | El gasto queda registrado en el sistema. |
| **Importancia** | Media |
| **Urgencia** | Media |
| **Comentarios** | Este caso de uso corresponde al proceso Registrar gastos identificado en el diagrama, y es realizado por el actor Contador (y en algunos casos por el Administrador). La información que se ingresa aquí es utilizada posteriormente en otros procesos como Generar estado de resultados. |

#### RF-12 — Consolidar Información Contable

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Camilo Andrés Meza De Ávila |
| **Objetivos asociados** | OB-14 Registrar y consolidar la información contable del sistema; OB-15 Generar reportes financieros y estados contables |
| **Requisitos asociados** | RI-29 Consolidación de información contable; RI-30 Integración de datos de inventario y nómina |
| **Descripción** | Integra datos de inventario y nómina. |
| **Precondición** | Existen datos en los módulos. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El sistema inicia proceso de consolidación |
| 2 | El sistema obtiene datos de inventario |
| 3 | El sistema obtiene datos de nómina |
| 4 | El sistema unifica la información |

**Excepción**

| Paso | Acción |
| --- | --- |
| 2 | Si algún módulo no tiene datos, el sistema continúa con datos disponibles |

| Campo | Valor |
| --- | --- |
| **Postcondición** | Información consolidada disponible para cálculos. |
| **Importancia** | Vital |
| **Urgencia** | Inmediata |
| **Comentarios** | Este caso de uso no se representó de forma directa en el diagrama, pero cumple una función interna esencial dentro del sistema, ya que se encarga de integrar datos provenientes de procesos como inventario y nómina, los cuales son necesarios para generar reportes contables. |

#### RF-13 — Calcular Balance General

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Camilo Andrés Meza De Ávila |
| **Objetivos asociados** | OB-15 Generar reportes financieros y estados contables |
| **Requisitos asociados** | RI-31 Cálculo de activos; RI-32 Cálculo de pasivos; RI-33 Cálculo de patrimonio |
| **Descripción** | Calcula activos, pasivos y patrimonio. |
| **Precondición** | Información contable consolidada. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El usuario solicita el balance general |
| 2 | El sistema toma los datos contables |
| 3 | El sistema realiza cálculos |
| 4 | El sistema muestra el balance |

**Excepción**

| Paso | Acción |
| --- | --- |
| 2 | Si faltan datos, el sistema muestra error |

| Campo | Valor |
| --- | --- |
| **Postcondición** | Se genera el balance general. |
| **Importancia** | Alta |
| **Urgencia** | Media |
| **Comentarios** | Este caso de uso forma parte de los procesos relacionados con la generación de información financiera, aunque no se encuentre explícitamente en el diagrama. Depende de datos previamente consolidados que provienen de otros casos de uso como gastos, inventario y nómina. |

#### RF-14 — Generar Reportes Contables

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Camilo Andrés Meza De Ávila |
| **Objetivos asociados** | OB-15 Generar reportes financieros y estados contables; OB-14 Registrar y consolidar la información contable del sistema |
| **Requisitos asociados** | RI-34 Generación de reportes financieros; RI-35 Exportación de reportes; RI-36 Visualización de información contable |
| **Descripción** | Genera y exporta reportes financieros. |
| **Precondición** | Información contable disponible. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El usuario solicita un reporte |
| 2 | El sistema recopila información |
| 3 | El sistema genera el reporte |
| 4 | El sistema muestra o exporta el reporte |

**Excepción**

| Paso | Acción |
| --- | --- |
| 2 | Si no hay datos el sistema muestra mensaje |

| Campo | Valor |
| --- | --- |
| **Postcondición** | Reporte generado correctamente. |
| **Importancia** | Alta |
| **Urgencia** | Media |
| **Comentarios** | Este caso de uso engloba la generación de diferentes informes financieros, incluyendo procesos como Generar estado de resultados, y es ejecutado principalmente por el actor Contador. Para su ejecución, requiere información de otros procesos como Registrar gastos, inventario y nómina, lo que evidencia una dependencia de datos. |

#### RF-15 — Gestionar Etiquetas

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Jesús Daniel Pérez Berrocal |
| **Objetivos asociados** | OB-04 Gestión de configuración del sistema; OB-05 Parametrización de procesos contables |
| **Requisitos asociados** | RI-04 Administración de etiquetas de producto; RI-05 Definición de impuestos y tasas contables |
| **Descripción** | Permite crear, editar y eliminar etiquetas contables. |
| **Precondición** | El usuario necesita rol de administrador o contador. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El usuario accede a la configuración. |
| 2 | Seleccionar las etiquetas a manipular. |
| 3 | Se realiza las acciones de crear, editar o eliminar. |
| 4 | El sistema guarda los cambios. |

**Excepción**

| Paso | Acción |
| --- | --- |
| 3 | Si hay datos inválidos, muestra error. |

| Campo | Valor |
| --- | --- |
| **Postcondición** | Las etiquetas quedan actualizadas. |
| **Importancia** | Alta |
| **Urgencia** | Inmediata |
| **Comentarios** | Proceso para la gestión de etiquetas contables. |

#### RF-16 — Ajustar Parámetros

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Jesús Daniel Pérez Berrocal |
| **Objetivos asociados** | OB-04 Gestión de configuración del sistema; OB-06 Adaptación a normativas legales |
| **Requisitos asociados** | RI-06 Configuración de valores legales (SMMLV, porcentajes); RI-07 Actualización de parámetros contables |
| **Descripción** | Permite modificar valores legales y porcentajes contables. |
| **Precondición** | El usuario necesita rol de administrador o contador. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | Accede a la configuración. |
| 2 | Selecciona los parámetros. |
| 3 | Modifica los valores digitados en porcentajes, o decimales. |
| 4 | Confirmar registro. |
| 5 | Guardar los cambios. |

**Excepción**

| Paso | Acción |
| --- | --- |
| 3 | Si el valor a registrar es inválido, muestra error. |

| Campo | Valor |
| --- | --- |
| **Postcondición** | Parámetros actualizados en el sistema. |
| **Importancia** | Alta |
| **Urgencia** | Inmediata |
| **Comentarios** | Proceso crítico para la gestión de información. |

#### RF-17 — Gestionar Usuarios del Sistema

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Jesús Daniel Pérez Berrocal |
| **Objetivos asociados** | OB-03 Administración de usuarios del sistema; OB-01 Control de acceso al sistema mediante autenticación |
| **Requisitos asociados** | RI-01 Gestión de información de usuarios; RI-03 Control de roles y permisos |
| **Descripción** | El sistema permitirá al usuario administrador gestionar los usuarios del sistema, incluyendo la creación, modificación y eliminación de cuentas, así como la asignación de roles y permisos correspondientes. |
| **Precondición** | El usuario debe haber iniciado sesión y contar con permisos de administrador. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El administrador accede al módulo de configuración |
| 2 | El sistema muestra las opciones de gestión |
| 3 | El administrador selecciona "Usuarios" |
| 4 | El sistema muestra la lista de usuarios registrados |
| 5 | El administrador selecciona una acción (crear, editar o eliminar) |
| 6 | El administrador selecciona "Agregar usuario" |
| 7 | El sistema muestra el formulario de registro |
| 8 | El administrador ingresa los datos (usuario, contraseña, rol) |
| 9 | El administrador confirma el registro |
| 10 | El sistema valida los datos |
| 11 | El sistema guarda el nuevo usuario |
| 12 | El administrador selecciona un usuario existente |
| 13 | Modifica los datos necesarios |
| 14 | Confirma los cambios |
| 15 | El sistema actualiza la información |
| 16 | El administrador selecciona un usuario |
| 17 | Confirma la eliminación |
| 18 | El sistema elimina el usuario |
| 19 | El sistema muestra un mensaje de confirmación |

**Excepción**

| Paso | Acción |
| --- | --- |
| 10 | Si el usuario no existe, el sistema muestra error. |
| 10 | Si la contraseña es incorrecta, el sistema muestra error. |
| 13 | Si el usuario no tiene permisos, el sistema bloquea el acceso. |
| 17 | Si el administrador cancela, no se realiza la eliminación. |
| 18 | Si el usuario es crítico (ej. administrador principal), el sistema impide eliminarlo. |

| Campo | Valor |
| --- | --- |
| **Postcondición** | Los usuarios del sistema quedan actualizados con los cambios realizados, incluyendo creación, modificación o eliminación. |
| **Importancia** | Alta |
| **Urgencia** | Inmediata |
| **Comentarios** | Este proceso es fundamental para garantizar la seguridad y control de acceso al sistema. |

#### RF-18 — Gestión de Roles y Permisos

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Jesús Daniel Pérez Berrocal |
| **Objetivos asociados** | OB-03 Administración de usuarios del sistema; OB-01 Control de acceso al sistema mediante autenticación |
| **Requisitos asociados** | RI-03 Control de roles y permisos; RI-08 Restricción de acceso a funcionalidades |
| **Descripción** | El sistema permitirá al usuario administrador gestionar los roles y permisos de los usuarios, definiendo el nivel de acceso a los diferentes módulos del sistema (Inventario, Nómina, Contabilidad y Configuración). |
| **Precondición** | El usuario debe haber iniciado sesión y contar con permisos de administrador. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El administrador accede al módulo de configuración |
| 2 | El sistema muestra las opciones de gestión |
| 3 | El administrador selecciona "Usuarios" |
| 4 | El sistema muestra la lista de usuarios registrados |
| 5 | El administrador selecciona una acción (crear, editar o eliminar) |
| 6 | El administrador selecciona "Agregar usuario" |
| 7 | El sistema muestra el formulario de registro |
| 8 | El administrador ingresa los datos (usuario, contraseña, rol) |
| 9 | El administrador confirma el registro |
| 10 | El sistema valida los datos |
| 11 | El sistema guarda el nuevo usuario |
| 12 | El administrador selecciona un usuario existente |
| 13 | Modifica los datos necesarios |
| 14 | Confirma los cambios |
| 15 | El sistema actualiza la información |
| 16 | El administrador selecciona un usuario |
| 17 | Confirma la eliminación |
| 18 | El sistema elimina el usuario |
| 19 | El sistema muestra un mensaje de confirmación |

**Excepción**

| Paso | Acción |
| --- | --- |
| 9 | Si no se selecciona ningún permiso, el sistema solicita configurarlo. |
| 12 | Si el nombre del rol existe, el sistema muestra error. |
| 17 | Si el administrador cancela, no se elimina el rol. |
| 18 | Si el rol esta asignado a usuarios, el sistema impide eliminarlo. |
| 18 | Si el usuario es crítico (ej. administrador principal), el sistema impide eliminarlo. |

| Campo | Valor |
| --- | --- |
| **Postcondición** | Los roles y permisos quedan actualizados, afectando el acceso de los usuarios a las funcionalidades del sistema. |
| **Importancia** | Alta |
| **Urgencia** | Inmediata |
| **Comentarios** | Este proceso es fundamental para garantizar la seguridad, control y segmentación de accesos dentro del sistema. |

#### RF-17 — Registrar Usuario

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Jesús Daniel Pérez Berrocal |
| **Objetivos asociados** | OB-03 Administración de Usuarios |
| **Requisitos asociados** | RI-03 Control de Acceso |
| **Descripción** | El sistema permitirá al administrador registrar nuevos usuarios asignándoles roles. |
| **Precondición** | El usuario necesita rol de administrador. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El usuario activa la opción "Recordar usuario". |
| 2 | El sistema guarda las credenciales. |
| 3 | En el siguiente inicio, el sistema carga los datos automáticamente. |
| 4 | Confirmar registro. |
| 5 | El sistema valida los datos y los guarda |

**Excepción**

| Paso | Acción |
| --- | --- |
| 5 | Si el usuario existe, el sistema muestra error. |
| 5 | Si hay campos vacíos, se solicita completar. |
| 5 | Si el formato es inválido, se muestra error. |

| Campo | Valor |
| --- | --- |
| **Postcondición** | El usuario queda registrado en el sistema. |
| **Importancia** | Alta |
| **Urgencia** | Inmediata |
| **Comentarios** | Proceso para la gestión de usuarios. |

#### RF-19 — Recordar Usuario

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Jesús Daniel Pérez Berrocal |
| **Objetivos asociados** | OB-02 Mejora de usabilidad |
| **Requisitos asociados** | RI-02 Persistencia de configuración |
| **Descripción** | El sistema permite recordar las credenciales del último usuario que inició sesión. |
| **Precondición** | El usuario ha iniciado sesión previamente. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El usuario activa la opción "Recordar usuario". |
| 2 | El sistema guarda las credenciales. |
| 3 | En el siguiente inicio, el sistema carga los datos automáticamente. |

**Excepción**

| Paso | Acción |
| --- | --- |
| 2 | Si ocurre un error al guardar, el sistema no almacena los datos. |

| Campo | Valor |
| --- | --- |
| **Postcondición** | Las credenciales quedan almacenadas para futuros accesos. |
| **Importancia** | Media |
| **Urgencia** | Media |
| **Comentarios** | Mejora la experiencia de usuario. |

#### RF-20 — Inicio de Sesión

| Campo | Valor |
| --- | --- |
| **Versión** | Versión 1.0 |
| **Autores** | Jesús Daniel Pérez Berrocal |
| **Objetivos asociados** | OB-01 Acceso seguro al sistema |
| **Requisitos asociados** | RI-01 Gestión de usuarios |
| **Descripción** | El sistema permitirá a los usuarios acceder a la aplicación mediante el ingreso de credenciales válidas (usuario y contraseña). |
| **Precondición** | El usuario debe disponer de rol administrativo o de gerencia para la edición de los permisos de los usuarios y roles. |

**Secuencia normal**

| Paso | Acción |
| --- | --- |
| 1 | El usuario abre la aplicación. |
| 2 | El sistema muestra el formulario de inicio de sesión. |
| 3 | El usuario selecciona "Iniciar sesión". |
| 4 | El sistema valida las credenciales. |
| 5 | El sistema permite el acceso al sistema. |

**Excepción**

| Paso | Acción |
| --- | --- |
| 5 | Si el usuario no existe, el sistema muestra error. |
| 5 | Si la contraseña es incorrecta, el sistema muestra error. |
| 5 | Si el usuario no tiene permisos, el sistema bloquea el acceso. |

| Campo | Valor |
| --- | --- |
| **Postcondición** | El usuario accede al sistema según su rol. |
| **Importancia** | Alta |
| **Urgencia** | Inmediata |
| **Comentarios** | Proceso crítico para la seguridad del sistema. |

---

## 8. Diagramas UML

### 8.1 Módulo de Inventario

#### 8.1.1 Requisito Funcional – 2 (Registro de nuevos productos)
- Diagrama de Estados 1
- Diagrama de Secuencia 1

#### 8.1.2 Requisito Funcional – 2 (Registrar entradas de inventario)
- Diagrama de Actividades 2
- Diagrama de Estados 2

#### 8.1.3 Requisito Funcional – 3 (Registrar Salidas de Inventario)
- Diagrama de Actividades 3
- Diagrama de Estados 3
- Diagrama de Secuencia 3

#### 8.1.4 Requisito Funcional – 4 (Clasificación de productos)
- Diagrama de Actividades 4
- Diagrama de Estados 4

#### 8.1.5 Requisito Funcional – 5 (Administración Integral de Productos)
- Diagrama de Actividades 5
- Diagrama de Estados 5

#### 8.1.6 Diagrama de Componentes – Módulo de Inventario
- Diagrama de Componentes 1

#### 8.1.7 Diagrama de Entidad/Relación – Módulo de Inventario
- Diagrama de Entidad/Relación 1

### 8.2 Módulo de Nómina

#### 8.2.1 Requisito Funcional – 6 (Registrar Empleados)
- Diagrama de Actividades 6
- Diagrama de Estados 6
- Diagrama de Comunicación 6
- Diagrama de Casos De Uso 6
- Diagrama de Secuencia 6
- Diagrama de Componentes 2
- Diagrama de Entidad/Relación 2

#### 8.2.2 Requisito Funcional – 7 (Eliminar Empleado)
- Diagrama de Actividades 7
- Diagrama de Estados 7
- Diagrama de Comunicación 7
- Diagrama de Casos De Uso 7
- Diagrama de Secuencia 7
- Diagrama de Componentes 3
- Diagrama de Entidad/Relación 3

#### 8.2.3 Requisito Funcional – 8 (Calcular Nómina)
- Diagrama de Actividades 8
- Diagrama de Estados 8
- Diagrama de Casos De Uso 8
- Diagrama de Secuencia 8
- Diagrama de Componentes 4
- Diagrama de Entidad/Relación 4

#### 8.2.4 Requisito Funcional – 9 (Registrar Novedades Laborales)
- Diagrama de Actividades 9
- Diagrama de Estados 9
- Diagrama de Casos De Uso 9
- Diagrama de Secuencia 9
- Diagrama de Componentes 5
- Diagrama de Entidad/Relación 5

### 8.3 Módulo de Contabilidad

#### 8.3.1 Requisito Funcional – 10 (Generar Estado de Resultados)
- Diagrama de Actividades 10
- Diagrama de Estados 10
- Diagrama de Comunicación 10
- Diagrama de Casos de Uso 10
- Diagrama de Secuencia 10
- Diagrama de Entidad-Relación 6
- Diagrama de Componentes 6

#### 8.3.2 Requisito Funcional – 11 (Registrar Gastos Deducibles)
- Diagrama de Actividades 11
- Diagrama de Estados 11
- Diagrama de Secuencia 11
- Diagrama de Comunicación 11
- Diagramas de Casos de Uso 11
- Diagrama de Entidad-Relación 7
- Diagrama de Componentes 7

#### 8.3.3 Requisito Funcional – 12 (Consolidar Información Contable)
- Diagrama de Actividades 12
- Diagrama de Estados 12
- Diagrama de Comunicación 12
- Diagrama de Casos de Uso 12
- Diagrama de Secuencia 12
- Diagrama de Entidad-Relación 8
- Diagrama de Componentes 8

#### 8.3.4 Requisito Funcional – 13 (Calcular Balance General)
- Diagrama de Actividades 13
- Diagrama de Estados 13
- Diagrama de Comunicación 13
- Diagrama de Casos de Uso 13
- Diagrama de Secuencia 13
- Diagrama de Entidad-Relación 9
- Diagrama de Componentes 9

#### 8.3.5 Requisito Funcional – 13 (Generar Reportes Contables)
- Diagrama de Actividades 14
- Diagrama de Estados 14
- Diagrama de Comunicación 14
- Diagrama de Casos de Usos 14
- Diagrama de Secuencia 14
- Diagrama de Entidad-Relación 10
- Diagrama de Componentes 10

### 8.4 Módulo de Configuración

#### 8.4.1 Requisito Funcional – 15 (Gestionar Etiquetas)
- Diagrama de Actividades 10
- Diagrama de Casos de Uso 11
- Diagrama de Estados 15
- Diagrama de Comunicación 10
- Diagrama de Secuencia 10
- Diagrama de Componentes 6

#### 8.4.2 Requisito Funcional – 16 (Ajustar Parámetros)
- Diagrama de Actividades 11
- Diagrama de Casos de Uso 12
- Diagrama de Estados 16
- Diagrama de Comunicación 11
- Diagrama de Componentes 7
- Diagrama de Secuencia 11

#### 8.4.3 Requisito Funcional – 17 (Gestionar Usuarios)
- Diagrama de Actividades 12
- Diagrama de Casos de Uso 13
- Diagrama de Estados 17
- Diagrama de Comunicación 12
- Diagrama de Componentes 8
- Diagrama de Secuencia 12

#### 8.4.4 Requisito Funcional – 18 (Gestionar Roles y Permisos)
- Diagrama de Actividades 13
- Diagrama de Casos de Uso 14
- Diagrama de Comunicación 13
- Diagrama de Estados 18
- Diagrama de Componentes 9
- Diagrama de Secuencia 13

#### 8.4.5 Diagrama de Entidad/Relación – Módulo de Configuración
- Diagrama de Entidad/Relación 1

### 8.5 Módulo de Seguridad

#### 8.5.1 Requisito Funcional – 19 (Iniciar Sesión)
- Diagrama de Actividades 14
- Diagrama de Casos de Uso 15
- Diagrama de Estados 19
- Diagrama de Comunicación 14
- Diagrama de Componentes 10
- Diagrama de Secuencia 14

#### 8.5.2 Requisito Funcional – 19 (Recordar Usuario)
- Diagrama de Actividades 15
- Diagrama de Casos de Uso 16
- Diagrama de Estados 20
- Diagrama de Comunicación 15
- Diagrama de Componentes 11
- Diagrama de Secuencia 15

#### 8.5.3 Diagrama de Entidad/Relación – Módulo de Seguridad
- Diagrama de Entidad/Relación 2

---

## 9. Diagrama De Gantt

> _(Espacio reservado para el diagrama de Gantt)_

---

## 10. Conclusión

El sistema Exodus Contable integra en una sola aplicación funciones administrativas, contables y de gestión, facilitando el manejo de la información en las PYMES. Gracias a los requisitos definidos y los diagramas UML, se logró organizar bien el funcionamiento del sistema y cómo interactúan los usuarios con cada módulo.

Además, los módulos de configuración y seguridad permiten controlar accesos y personalizar el sistema, haciendo que sea más confiable y útil. En general, el proyecto muestra cómo una buena organización y diseño ayudan a crear una solución práctica y funcional.

<?php
/**
 * config/db.php
 *
 * Este es el ÚNICO archivo que sabe cómo conectarse a MySQL.
 * Ningún HTML/JS puede leer este archivo: vive en el servidor,
 * PHP lo interpreta y nunca envía su contenido al navegador.
 *
 * PDO::ATTR_EMULATE_PREPARES => false obliga a que las consultas
 * preparadas sean preparadas de VERDAD por MySQL (bindeadas), no
 * simuladas por PHP. Así los valores nunca se concatenan al SQL:
 * esto es lo que evita la inyección SQL.
 */

$host    = 'localhost';
$db      = 'exodus_nomina';
$user    = 'root';   // usuario por defecto de XAMPP
$pass    = '';       // XAMPP no trae contraseña por defecto
$charset = 'utf8mb4';

$dsn = "mysql:host={$host};dbname={$db};charset={$charset}";

$opciones = [
    PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    PDO::ATTR_EMULATE_PREPARES   => false,
];

try {
    $pdo = new PDO($dsn, $user, $pass, $opciones);
} catch (PDOException $e) {
    http_response_code(500);
    header('Content-Type: application/json; charset=utf-8');
    die(json_encode([
        'error' => 'No se pudo conectar a la base de datos. Revisa que MySQL esté '
                 . 'corriendo en XAMPP y que exodus_nomina.sql haya sido importado.',
        'detalle' => $e->getMessage(),
    ]));
}

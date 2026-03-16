-- ============================================================
-- SEEDS — E-COMMERCE PERSIANAS Y CORTINAS DANY
-- PostgreSQL + pgcrypto (BCrypt factor 10)
-- ============================================================
-- Orden de ejecución:
--   1. Habilitar extensión pgcrypto
--   2. Datos de lookup (ya en schema, aquí se refuerzan con ON CONFLICT)
--   3. Ubicación (departamento + ciudad)
--   4. Usuarios (admin + clientes)
--   5. Clientes y direcciones
--   6. Categorías + guías de medidas
--   7. Productos + imágenes
-- ============================================================

-- ── 1. EXTENSIÓN PGCRYPTO ────────────────────────────────────────────────────
-- Necesaria para crypt() y gen_salt() que generan el hash BCrypt
CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- ── 2. DATOS DE LOOKUP ───────────────────────────────────────────────────────
-- Se usan ON CONFLICT para que el script sea re-ejecutable sin errores

INSERT INTO Roles (rol_id, nombre) VALUES
    (1, 'admin'),
    (2, 'cliente')
ON CONFLICT (rol_id) DO NOTHING;

INSERT INTO EstadosPedido (estado_id, nombre) VALUES
    (1, 'Pendiente de preparación'),
    (2, 'Preparado'),
    (3, 'Enviado')
ON CONFLICT (estado_id) DO NOTHING;

INSERT INTO MetodosPago (metodo_id, nombre) VALUES
    (1, 'Tarjeta débito'),
    (2, 'Tarjeta crédito'),
    (3, 'PSE')
ON CONFLICT (metodo_id) DO NOTHING;


-- ── 3. UBICACIÓN ─────────────────────────────────────────────────────────────

INSERT INTO Departamentos (departamento_id, nombre) VALUES
    (1, 'Meta'),
    (2, 'Cundinamarca'),
    (3, 'Antioquia'),
    (4, 'Valle del Cauca')
ON CONFLICT (departamento_id) DO NOTHING;

INSERT INTO Ciudades (ciudad_id, nombre, departamento_id) VALUES
    (1, 'Villavicencio',  1),
    (2, 'Granada',        1),
    (3, 'Bogotá',         2),
    (4, 'Medellín',       3),
    (5, 'Cali',           4)
ON CONFLICT (ciudad_id) DO NOTHING;


-- ── 4. USUARIOS ──────────────────────────────────────────────────────────────
-- Contraseñas hasheadas con BCrypt factor 10 usando pgcrypto.
-- Formato: crypt('contraseña_plana', gen_salt('bf', 10))
--
--   admin@dany.com        → Admin2024$
--   cliente1@example.com  → Cliente123$
--   cliente2@example.com  → Cliente123$
--
-- Para verificar en backend (Node.js / bcrypt):
--   bcrypt.compare('Admin2024$', hash_almacenado)  → true

INSERT INTO Usuarios (usuario_id, nombre, email, contrasena, proveedor_auth, rol_id, activo) VALUES
(
    1,
    'Administrador Dany',
    'admin@cortinasydany.com',
    crypt('Admin2024$', gen_salt('bf', 10)),
    'local',
    1,   -- rol admin
    TRUE
),
(
    2,
    'María Pérez',
    'maria.perez@example.com',
    crypt('Cliente123$', gen_salt('bf', 10)),
    'local',
    2,   -- rol cliente
    TRUE
),
(
    3,
    'Carlos Rodríguez',
    'carlos.rodriguez@example.com',
    crypt('Cliente123$', gen_salt('bf', 10)),
    'local',
    2,
    TRUE
),
(
    4,
    'Laura Gómez',
    'laura.gomez@gmail.com',
    NULL,                -- usuario OAuth → no tiene contraseña local
    'google',
    2,
    TRUE
)
ON CONFLICT (usuario_id) DO NOTHING;

-- Resetear secuencia para que los próximos inserts no colisionen
SELECT setval('usuarios_usuario_id_seq', (SELECT MAX(usuario_id) FROM Usuarios));


-- ── 5. CLIENTES Y DIRECCIONES ────────────────────────────────────────────────

INSERT INTO Clientes (cliente_id, usuario_id, telefono, documento_tipo, documento_numero) VALUES
    (1, 2, '3201234567', 'CC', '1020304050'),   -- María Pérez
    (2, 3, '3109876543', 'CC', '1098765432'),   -- Carlos Rodríguez
    (3, 4, '3155556677', 'CC', '1065432198')    -- Laura Gómez (OAuth)
ON CONFLICT (cliente_id) DO NOTHING;

SELECT setval('clientes_cliente_id_seq', (SELECT MAX(cliente_id) FROM Clientes));

INSERT INTO Direcciones (direccion_id, cliente_id, ciudad_id, barrio, calle, numero, complemento, es_principal) VALUES
    (1, 1, 1, 'Barzal Alto',    'Calle 35',    '# 28-14', 'Apto 301', TRUE),
    (2, 2, 1, 'La Rosita',      'Carrera 42',  '# 15-60', NULL,       TRUE),
    (3, 3, 3, 'Chapinero',      'Calle 67',    '# 7-30',  'Casa',     TRUE)
ON CONFLICT (direccion_id) DO NOTHING;

SELECT setval('direcciones_direccion_id_seq', (SELECT MAX(direccion_id) FROM Direcciones));


-- ── 6. CATEGORÍAS Y GUÍAS DE MEDIDAS ────────────────────────────────────────

INSERT INTO Categorias (categoria_id, nombre, descripcion, activo) VALUES
    (1, 'Cortinas',    'Telas de caída elegante para ambientes clásicos y modernos', TRUE),
    (2, 'Persianas',   'Sistemas enrollables y venecianos para control de luz',      TRUE),
    (3, 'Paneles',     'Paneles deslizantes japoneses y divisores de ambientes',     TRUE),
    (4, 'Accesorios',  'Rieles, bastones, grapas y complementos de instalación',    TRUE)
ON CONFLICT (categoria_id) DO NOTHING;

SELECT setval('categorias_categoria_id_seq', (SELECT MAX(categoria_id) FROM Categorias));

INSERT INTO GuiaMedidas (guia_id, categoria_id, instrucciones, video_url, margen_ancho_cm, margen_alto_cm) VALUES
(
    1, 1,
    'Para cortinas, mide el ancho del riel o barra donde se instalará la cortina. Para el alto, mide desde la parte superior del riel hasta donde deseas que llegue (suelo, repisa o punto intermedio). Se recomienda agregar al menos 20 cm al ancho para efecto de vuelo y 5 cm al alto para el dobladillo superior.',
    'https://www.youtube.com/embed/ejemplo_cortinas',
    20, 5
),
(
    2, 2,
    'Para persianas enrollables, mide el ancho interno del vano de pared a pared y el alto desde el techo hasta el suelo. El sistema se instala dentro del vano. Descuenta 1 cm del ancho medido para asegurar un ajuste perfecto sin rozamientos.',
    'https://www.youtube.com/embed/ejemplo_persianas',
    -1, 0
),
(
    3, 3,
    'Los paneles japoneses se instalan en rieles de techo. Mide el ancho total del vano y el alto desde el riel hasta el suelo. Cada panel tiene un ancho fijo; el sistema calcula cuántos paneles necesitas según el ancho medido.',
    'https://www.youtube.com/embed/ejemplo_paneles',
    0, 2
),
(
    4, 4,
    'Para accesorios como rieles y bastones, mide el ancho del vano o la ventana sobre la que se instalará. Generalmente se añaden 15-20 cm a cada lado para el soporte de los soportes laterales.',
    NULL,
    30, 0
)
ON CONFLICT (guia_id) DO NOTHING;

SELECT setval('guiamedidas_guia_id_seq', (SELECT MAX(guia_id) FROM GuiaMedidas));


-- ── 7. PRODUCTOS ─────────────────────────────────────────────────────────────

INSERT INTO Productos (producto_id, nombre, descripcion, precio_m2, categoria_id, activo) VALUES

-- Cortinas (categoria_id = 1)
(
    1,
    'Cortina Clásica',
    'Cortina de tela resistente con caída elegante. Disponible en múltiples colores y texturas. Fabricación artesanal con acabados de lujo. Ideal para salas, comedores y habitaciones.',
    120000.00, 1, TRUE
),
(
    2,
    'Cortina Blackout',
    'Tela técnica de doble capa que bloquea hasta el 99% de la luz solar. Perfecta para habitaciones, salas de cine en casa y espacios que requieren oscuridad total.',
    160000.00, 1, TRUE
),
(
    3,
    'Cortina Sheer',
    'Tela translúcida que filtra la luz suavemente creando ambientes luminosos sin perder privacidad. Efecto etéreo ideal para comedores y salas.',
    95000.00, 1, TRUE
),

-- Persianas (categoria_id = 2)
(
    4,
    'Persiana Enrollable',
    'Sistema enrollable de tela técnica con mecanismo de cadena de alta durabilidad. Control preciso de la entrada de luz. Disponible en telas screen, blackout y traslúcida.',
    180000.00, 2, TRUE
),
(
    5,
    'Persiana Veneciana',
    'Lamas horizontales de aluminio de 25mm o 50mm. Control total de la inclinación para regular luz y privacidad. Resistente a la humedad, ideal para baños y cocinas.',
    140000.00, 2, TRUE
),
(
    6,
    'Persiana Zebra',
    'Combinación de bandas opacas y translúcidas que al superponerse permiten un control gradual de la luz. Diseño moderno y minimalista para espacios contemporáneos.',
    200000.00, 2, TRUE
),

-- Paneles (categoria_id = 3)
(
    7,
    'Panel Japonés',
    'Paneles deslizantes de tela montados en rieles de aluminio. Aportan un look oriental minimalista y funcionan como divisores de ambientes o cubrimiento de ventanas grandes.',
    250000.00, 3, TRUE
),
(
    8,
    'Panel Roller Screen',
    'Panel en tela screen técnica que permite ver el exterior sin que el exterior vea hacia adentro durante el día. Excelente para oficinas y espacios con vista panorámica.',
    220000.00, 3, TRUE
),

-- Accesorios (categoria_id = 4)
(
    9,
    'Riel de Aluminio Doble',
    'Riel de aluminio extruido doble vía para instalar cortinas con velo. Acabado anodizado. Incluye deslizadores, topes y soporte de techo. Medida por metro lineal.',
    45000.00, 4, TRUE
),
(
    10,
    'Bastón Decorativo',
    'Bastón de acero inoxidable con terminales decorativos. Diámetro 28mm. Compatible con aritos y pinzas. Instalación rápida con soporte de pared incluido.',
    38000.00, 4, TRUE
)

ON CONFLICT (producto_id) DO NOTHING;

SELECT setval('productos_producto_id_seq', (SELECT MAX(producto_id) FROM Productos));


-- ── 8. IMÁGENES DE PRODUCTOS ─────────────────────────────────────────────────
-- URLs de Cloudinary — reemplazar por las URLs reales al subir las fotos
-- Por ahora se usan URLs de ejemplo con el mismo patrón

INSERT INTO ImagenesProducto (imagen_id, producto_id, url, es_principal, orden) VALUES

-- Cortina Clásica
(1,  1, 'https://res.cloudinary.com/dany/image/upload/v1/cortinas/cortina-clasica-1.webp',  TRUE,  1),
(2,  1, 'https://res.cloudinary.com/dany/image/upload/v1/cortinas/cortina-clasica-2.webp',  FALSE, 2),
(3,  1, 'https://res.cloudinary.com/dany/image/upload/v1/cortinas/cortina-clasica-3.webp',  FALSE, 3),

-- Cortina Blackout
(4,  2, 'https://res.cloudinary.com/dany/image/upload/v1/cortinas/cortina-blackout-1.webp', TRUE,  1),
(5,  2, 'https://res.cloudinary.com/dany/image/upload/v1/cortinas/cortina-blackout-2.webp', FALSE, 2),

-- Cortina Sheer
(6,  3, 'https://res.cloudinary.com/dany/image/upload/v1/cortinas/cortina-sheer-1.webp',    TRUE,  1),

-- Persiana Enrollable
(7,  4, 'https://res.cloudinary.com/dany/image/upload/v1/persianas/enrollable-1.webp',      TRUE,  1),
(8,  4, 'https://res.cloudinary.com/dany/image/upload/v1/persianas/enrollable-2.webp',      FALSE, 2),

-- Persiana Veneciana
(9,  5, 'https://res.cloudinary.com/dany/image/upload/v1/persianas/veneciana-1.webp',       TRUE,  1),

-- Persiana Zebra
(10, 6, 'https://res.cloudinary.com/dany/image/upload/v1/persianas/zebra-1.webp',           TRUE,  1),
(11, 6, 'https://res.cloudinary.com/dany/image/upload/v1/persianas/zebra-2.webp',           FALSE, 2),

-- Panel Japonés
(12, 7, 'https://res.cloudinary.com/dany/image/upload/v1/paneles/japones-1.webp',           TRUE,  1),
(13, 7, 'https://res.cloudinary.com/dany/image/upload/v1/paneles/japones-2.webp',           FALSE, 2),

-- Panel Roller Screen
(14, 8, 'https://res.cloudinary.com/dany/image/upload/v1/paneles/screen-1.webp',            TRUE,  1),

-- Riel de Aluminio Doble
(15, 9, 'https://res.cloudinary.com/dany/image/upload/v1/accesorios/riel-aluminio-1.webp',  TRUE,  1),

-- Bastón Decorativo
(16, 10, 'https://res.cloudinary.com/dany/image/upload/v1/accesorios/baston-1.webp',        TRUE,  1)

ON CONFLICT (imagen_id) DO NOTHING;

SELECT setval('imagenesproducto_imagen_id_seq', (SELECT MAX(imagen_id) FROM ImagenesProducto));


-- ============================================================
-- VERIFICACIÓN RÁPIDA
-- Ejecuta estas consultas para confirmar que los seeds
-- se insertaron correctamente
-- ============================================================

/*
-- Usuarios con roles
SELECT u.usuario_id, u.nombre, u.email, u.proveedor_auth, r.nombre AS rol,
       CASE WHEN u.contrasena IS NOT NULL THEN 'sí' ELSE 'no (OAuth)' END AS tiene_password
FROM Usuarios u
JOIN Roles r ON u.rol_id = r.rol_id
ORDER BY u.usuario_id;

-- Productos por categoría con precio
SELECT p.producto_id, p.nombre, c.nombre AS categoria,
       TO_CHAR(p.precio_m2, 'FM$999,999,999') AS precio_m2,
       (SELECT COUNT(*) FROM ImagenesProducto WHERE producto_id = p.producto_id) AS imagenes
FROM Productos p
JOIN Categorias c ON p.categoria_id = c.categoria_id
ORDER BY c.nombre, p.producto_id;

-- Verificar hash BCrypt del admin (debe devolver el hash, no NULL)
SELECT email, LEFT(contrasena, 30) || '...' AS hash_preview
FROM Usuarios WHERE proveedor_auth = 'local';
*/


-- ============================================================
-- DEPARTAMENTOS Y CIUDADES (pruebas — 5 registros)
-- ============================================================

INSERT INTO Departamentos (nombre) VALUES
    ('Meta'),
    ('Cundinamarca'),
    ('Antioquia'),
    ('Valle del Cauca'),
    ('Atlántico')
ON CONFLICT DO NOTHING;

INSERT INTO Ciudades (nombre, departamento_id) VALUES
    ('Villavicencio',  1),
    ('Granada',        1),
    ('Bogotá',         2),
    ('Medellín',       3),
    ('Cali',           4)
ON CONFLICT DO NOTHING;

SELECT setval('departamentos_departamento_id_seq', (SELECT MAX(departamento_id) FROM Departamentos));
SELECT setval('ciudades_ciudad_id_seq',            (SELECT MAX(ciudad_id)       FROM Ciudades));

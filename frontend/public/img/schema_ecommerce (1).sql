-- ==========================================
-- E-COMMERCE PERSIANAS Y CORTINAS DANY
-- Script de creación de base de datos
-- PostgreSQL
-- ==========================================

-- ── ROLES Y USUARIOS ──────────────────────────────────────────────────────────

CREATE TABLE Roles (
    rol_id  SERIAL PRIMARY KEY,
    nombre  VARCHAR(50) NOT NULL
    -- Valores: 'admin', 'cliente'
);

CREATE TABLE Usuarios (
    usuario_id      SERIAL PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    email           VARCHAR(150) UNIQUE NOT NULL,
    contrasena      VARCHAR(255),                    -- Hash BCrypt. NULL si usa Google o Microsoft
    proveedor_auth  VARCHAR(20) NOT NULL DEFAULT 'local', -- 'local' | 'google' | 'microsoft'
    proveedor_id    VARCHAR(255),                    -- ID externo del proveedor OAuth. NULL si es local
    rol_id          INT REFERENCES Roles(rol_id) DEFAULT 2, -- 2 = cliente por defecto
    activo          BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_registro  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE Clientes (
    cliente_id       SERIAL PRIMARY KEY,
    usuario_id       INT UNIQUE REFERENCES Usuarios(usuario_id),
    telefono         VARCHAR(20),
    documento_tipo   VARCHAR(20),                    -- CC | NIT | CE | pasaporte
    documento_numero VARCHAR(30)                     -- Requerido para factura DIAN
);

-- ── UBICACIÓN ─────────────────────────────────────────────────────────────────

CREATE TABLE Departamentos (
    departamento_id SERIAL PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL
);

CREATE TABLE Ciudades (
    ciudad_id       SERIAL PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    departamento_id INT REFERENCES Departamentos(departamento_id)
);

CREATE TABLE Direcciones (
    direccion_id SERIAL PRIMARY KEY,
    cliente_id   INT REFERENCES Clientes(cliente_id),
    ciudad_id    INT REFERENCES Ciudades(ciudad_id),
    barrio       VARCHAR(100),
    calle        VARCHAR(150),
    numero       VARCHAR(50),
    complemento  VARCHAR(150),
    es_principal BOOLEAN DEFAULT FALSE               -- Dirección predeterminada del cliente
);

-- ── CATÁLOGO ──────────────────────────────────────────────────────────────────

CREATE TABLE Categorias (
    categoria_id SERIAL PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL,
    descripcion  TEXT,
    activo       BOOLEAN NOT NULL DEFAULT TRUE
);


CREATE TABLE Productos (
    producto_id    SERIAL PRIMARY KEY,
    nombre         VARCHAR(150) NOT NULL,
    descripcion    TEXT,
    precio_m2      DECIMAL(10,2) NOT NULL,           -- Precio por m², definido y modificable por el admin
    categoria_id   INT REFERENCES Categorias(categoria_id),
    activo         BOOLEAN NOT NULL DEFAULT TRUE,    -- RF-18: activar/desactivar visibilidad en tienda
    fecha_creacion TIMESTAMP DEFAULT NOW()
);

-- Galería de imágenes por producto (RF-17, CU-02)
CREATE TABLE ImagenesProducto (
    imagen_id    SERIAL PRIMARY KEY,
    producto_id  INT REFERENCES Productos(producto_id) ON DELETE CASCADE,
    url          VARCHAR(255) NOT NULL,              -- URL de Cloudinary
    es_principal BOOLEAN DEFAULT FALSE,              -- Imagen principal de la card del catálogo
    orden        INT DEFAULT 0                       -- Orden en la galería de detalle
);

-- ── PEDIDOS ───────────────────────────────────────────────────────────────────

CREATE TABLE EstadosPedido (
    estado_id SERIAL PRIMARY KEY,
    nombre    VARCHAR(50) NOT NULL
    -- Valores: 'Pendiente de preparación', 'Preparado', 'Enviado'
);

CREATE TABLE Pedidos (
    pedido_id       SERIAL PRIMARY KEY,
    cliente_id      INT REFERENCES Clientes(cliente_id),
    direccion_id    INT REFERENCES Direcciones(direccion_id),
    estado_id       INT REFERENCES EstadosPedido(estado_id),
    fecha_pedido    TIMESTAMP NOT NULL DEFAULT NOW(),
    total           DECIMAL(10,2) NOT NULL,          -- Suma de precio_total de todos los ítems
    referencia_pago VARCHAR(100),                    -- ID de transacción devuelto por la pasarela
    notas           TEXT                             -- Observaciones adicionales del cliente
);

-- Detalle del pedido con medidas y cálculo de precio por m² (RF-05, RF-06)
CREATE TABLE DetallePedido (
    detalle_id   SERIAL PRIMARY KEY,
    pedido_id    INT REFERENCES Pedidos(pedido_id) ON DELETE CASCADE,
    producto_id  INT REFERENCES Productos(producto_id),
    cantidad     INT NOT NULL DEFAULT 1,
    ancho_cm     DECIMAL(8,2) NOT NULL,              -- Ancho del vano ingresado por el cliente (cm)
    alto_cm      DECIMAL(8,2) NOT NULL,              -- Alto del vano ingresado por el cliente (cm)
    area_m2      DECIMAL(10,4) NOT NULL,             -- Calculado: (ancho_cm × alto_cm) / 10000
    precio_m2    DECIMAL(10,2) NOT NULL,             -- Snapshot del precio/m² al momento del pedido
    precio_total DECIMAL(10,2) NOT NULL              -- Calculado: area_m2 × precio_m2 × cantidad
);

-- ── PAGOS ─────────────────────────────────────────────────────────────────────

CREATE TABLE MetodosPago (
    metodo_id SERIAL PRIMARY KEY,
    nombre    VARCHAR(50) NOT NULL
    -- Valores: 'Tarjeta débito', 'Tarjeta crédito', 'PSE'
);

CREATE TABLE Pagos (
    pago_id              SERIAL PRIMARY KEY,
    pedido_id            INT UNIQUE REFERENCES Pedidos(pedido_id), -- Un pago por pedido
    metodo_id            INT REFERENCES MetodosPago(metodo_id),
    monto                DECIMAL(10,2) NOT NULL,
    fecha_pago           TIMESTAMP NOT NULL DEFAULT NOW(),
    estado_pago          VARCHAR(50) NOT NULL,       -- aprobado | rechazado | pendiente
    referencia_pasarela  VARCHAR(100)                -- ID interno de la pasarela (Wompi transaction ID)
);

-- ── FACTURACIÓN ELECTRÓNICA DIAN ─────────────────────────────────────────────

CREATE TABLE Facturas (
    factura_id        SERIAL PRIMARY KEY,
    pedido_id         INT UNIQUE REFERENCES Pedidos(pedido_id), -- Una factura por pedido
    numero_factura    VARCHAR(50) NOT NULL,          -- Número consecutivo de factura electrónica
    cufe              VARCHAR(255) NOT NULL,         -- Código Único de Factura Electrónica - DIAN
    xml_path          VARCHAR(255),                  -- Ruta/URL del XML firmado transmitido a la DIAN
    pdf_path          VARCHAR(255),                  -- Ruta/URL del PDF generado para el cliente
    enviada_dian      BOOLEAN NOT NULL DEFAULT FALSE,-- Confirmación de transmisión exitosa a la DIAN
    estado            VARCHAR(50),                   -- generada | transmitida | aceptada | rechazada
    fecha_emision     TIMESTAMP NOT NULL DEFAULT NOW(),
    fecha_vencimiento DATE                           -- Fecha límite de pago si aplica
);

-- ── NOTIFICACIONES AL ADMIN ───────────────────────────────────────────────────

-- Log de correos enviados al admin al confirmar un pago (RF-22)
CREATE TABLE NotificacionesAdmin (
    notif_id      SERIAL PRIMARY KEY,
    pedido_id     INT REFERENCES Pedidos(pedido_id),
    destinatario  VARCHAR(150) NOT NULL,             -- Correo del administrador
    estado        VARCHAR(50) NOT NULL,              -- enviado | fallido | reintentando
    fecha_envio   TIMESTAMP NOT NULL DEFAULT NOW(),
    intentos      INT DEFAULT 1,                     -- Número de intentos de envío
    error_detalle TEXT                               -- Detalle del error si el envío falló
);

-- ==========================================
-- DATOS INICIALES
-- ==========================================

INSERT INTO Roles (nombre) VALUES ('admin'), ('cliente');

INSERT INTO EstadosPedido (nombre) VALUES
    ('Pendiente de preparación'),
    ('Preparado'),
    ('Enviado');

INSERT INTO MetodosPago (nombre) VALUES
    ('Tarjeta débito'),
    ('Tarjeta crédito'),
    ('PSE');

-- ── CARRITO PERSISTENTE ───────────────────────────────────────────────────────

CREATE TABLE CarritoItems (
    item_id        SERIAL PRIMARY KEY,
    usuario_id     INT REFERENCES Usuarios(usuario_id) ON DELETE CASCADE,
    producto_id    INT REFERENCES Productos(producto_id) ON DELETE CASCADE,
    cantidad       INT NOT NULL DEFAULT 1,
    ancho_cm       DECIMAL(8,2) NOT NULL,
    alto_cm        DECIMAL(8,2) NOT NULL,
    area_m2        DECIMAL(10,4) NOT NULL,           -- (ancho_cm × alto_cm) / 10000
    fecha_agregado TIMESTAMP DEFAULT NOW(),
    UNIQUE (usuario_id, producto_id, ancho_cm, alto_cm) -- evita duplicados exactos
);

-- ── ÍNDICES ───────────────────────────────────────────────────────────────────

CREATE INDEX idx_productos_activo      ON Productos(activo);
CREATE INDEX idx_productos_categoria   ON Productos(categoria_id);
CREATE INDEX idx_imagenes_producto     ON ImagenesProducto(producto_id, orden);
CREATE INDEX idx_pedidos_cliente       ON Pedidos(cliente_id);
CREATE INDEX idx_detalle_pedido        ON DetallePedido(pedido_id);
CREATE INDEX idx_carrito_usuario       ON CarritoItems(usuario_id);

CREATE DATABASE icc115
	CHARACTER SET utf8mb4
	COLLATE utf8mb4_spanish_ci;

CREATE TABLE users (
    user_id BINARY(16) PRIMARY KEY DEFAULT (UUID_TO_BIN(UUID())),
    nombre varchar(255),
    email varchar(255),
    telefono varchar(20),
    direccion varchar(255),
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE billing_data (
    billing_id BINARY(16) PRIMARY KEY DEFAULT (UUID_TO_BIN(UUID())),
    user_id BINARY(16),
    fecha_factura DATE,
    monto REAL,
    estado varchar(25),
    servicio varchar(50),
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE conversations (
    session_id BINARY(16) PRIMARY KEY DEFAULT (UUID_TO_BIN(UUID())),
    user_id BINARY(16),
    fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_fin TIMESTAMP,
    satisfaccion INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE messages (
    message_id BINARY(16) PRIMARY KEY DEFAULT (UUID_TO_BIN(UUID())),
    session_id BINARY(16),
    sender varchar(8),
    text varchar(255),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(session_id) REFERENCES conversations(session_id)
);

CREATE TABLE support_tickets (
    ticket_id BINARY(16) PRIMARY KEY DEFAULT (UUID_TO_BIN(UUID())),
    user_id BINARY(16),
    problema varchar(100),
    descripcion varchar(255),
    estado varchar(15),
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fecha_cierre TIMESTAMP,
    prioridad varchar(15),
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE technical_visits (
    visit_id BINARY(16) PRIMARY KEY DEFAULT (UUID_TO_BIN(UUID())),
    ticket_id BINARY(16),
    user_id BINARY(16),
    fecha_visita TIMESTAMP,
    tecnico BINARY(16),
    estado varchar(20),
    FOREIGN KEY(ticket_id) REFERENCES support_tickets(ticket_id),
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

CREATE TABLE feedback (
    feedback_id BINARY(16) PRIMARY KEY DEFAULT (UUID_TO_BIN(UUID())),
    session_id BINARY(16),
    user_id BINARY(16),
    rating INTEGER,
    comentarios varchar(255),
    fecha_feedback TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(session_id) REFERENCES conversations(session_id),
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);


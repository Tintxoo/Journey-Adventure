import sqlite3
from pathlib import Path


_ESQUEMA = """
CREATE TABLE IF NOT EXISTS roles (
    id_rol INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_rol TEXT NOT NULL,
    descripcion TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    id_rol INTEGER NOT NULL REFERENCES roles(id_rol),
    nombre_completo TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    documento_identidad TEXT NOT NULL UNIQUE,
    telefono TEXT NOT NULL,
    intentos_fallidos INTEGER NOT NULL CHECK (intentos_fallidos >= 0),
    activo INTEGER NOT NULL CHECK (activo IN (0, 1)),
    fecha_registro TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS destinos (
    id_destino INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    pais TEXT NOT NULL,
    ciudad TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    costo_base TEXT NOT NULL,
    disponible INTEGER NOT NULL CHECK (disponible IN (0, 1)),
    fecha_creacion TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS paquetes_turisticos (
    id_paquete INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_paquete TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    fecha_inicio TEXT NOT NULL,
    fecha_fin TEXT NOT NULL,
    costo_total TEXT NOT NULL,
    cupos_totales INTEGER NOT NULL CHECK (cupos_totales >= 0),
    cupos_disponibles INTEGER NOT NULL CHECK (cupos_disponibles >= 0),
    estado TEXT NOT NULL,
    CHECK (cupos_disponibles <= cupos_totales),
    CHECK (fecha_fin >= fecha_inicio)
);
CREATE TABLE IF NOT EXISTS paquete_destinos (
    id_paquete_destino INTEGER PRIMARY KEY AUTOINCREMENT,
    id_paquete INTEGER NOT NULL REFERENCES paquetes_turisticos(id_paquete),
    id_destino INTEGER NOT NULL REFERENCES destinos(id_destino),
    orden_itinerario INTEGER NOT NULL CHECK (orden_itinerario > 0),
    dias_estadia INTEGER NOT NULL CHECK (dias_estadia > 0),
    costo_asignado TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS actividades_paquete (
    id_actividad INTEGER PRIMARY KEY AUTOINCREMENT,
    id_paquete INTEGER NOT NULL REFERENCES paquetes_turisticos(id_paquete) ON DELETE CASCADE,
    nombre TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    dia_relativo INTEGER NOT NULL
        CHECK (typeof(dia_relativo) = 'integer' AND dia_relativo >= 1)
);
CREATE TABLE IF NOT EXISTS reservas (
    id_reserva INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo_reserva TEXT NOT NULL UNIQUE,
    id_usuario INTEGER NOT NULL REFERENCES usuarios(id_usuario),
    id_paquete INTEGER NOT NULL REFERENCES paquetes_turisticos(id_paquete),
    fecha_reserva TEXT NOT NULL,
    cantidad_personas INTEGER NOT NULL CHECK (cantidad_personas > 0),
    monto_total TEXT NOT NULL,
    estado_reserva TEXT NOT NULL,
    observaciones TEXT
);
CREATE TABLE IF NOT EXISTS pasajeros (
    id_pasajero INTEGER PRIMARY KEY AUTOINCREMENT,
    id_reserva INTEGER NOT NULL REFERENCES reservas(id_reserva),
    nombre_completo TEXT NOT NULL,
    documento_identidad TEXT NOT NULL,
    fecha_nacimiento TEXT NOT NULL,
    telefono_contacto TEXT NOT NULL,
    es_titular INTEGER NOT NULL CHECK (es_titular IN (0, 1))
);
"""


def crear_base_datos(
    ruta: str | Path = "data/journey_adventure.sqlite3",
) -> sqlite3.Connection:
    if str(ruta) != ":memory:":
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)

    conexion = sqlite3.connect(str(ruta))
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    conexion.executescript(_ESQUEMA)
    conexion.commit()
    return conexion


def main() -> None:
    conexion = crear_base_datos()
    conexion.close()
    print("Base de datos creada en data/journey_adventure.sqlite3")


if __name__ == "__main__":
    main()

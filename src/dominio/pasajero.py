from dataclasses import dataclass
from datetime import date
from typing import ClassVar


@dataclass
class Pasajero:
    id_pasajero: int | None = None
    id_reserva: int = 0
    nombre_completo: str = ""
    documento_identidad: str = ""
    fecha_nacimiento: date = date.min
    telefono_contacto: str = ""
    es_titular: bool = False

    tabla: ClassVar[str] = "pasajeros"
    clave_primaria: ClassVar[str] = "id_pasajero"

    def validar_datos(self) -> bool:
        return bool(self.nombre_completo.strip() and self.documento_identidad.strip())

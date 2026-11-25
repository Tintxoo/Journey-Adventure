from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import ClassVar


@dataclass
class Reserva:
    id_reserva: int | None = None
    codigo_reserva: str = ""
    id_usuario: int = 0
    id_paquete: int = 0
    fecha_reserva: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    cantidad_personas: int = 1
    monto_total: Decimal = Decimal("0")
    estado_reserva: str = "pendiente"
    observaciones: str | None = None

    tabla: ClassVar[str] = "reservas"
    clave_primaria: ClassVar[str] = "id_reserva"

    def validar(self) -> bool:
        return bool(
            self.codigo_reserva.strip()
            and self.id_usuario > 0
            and self.id_paquete > 0
            and self.cantidad_personas > 0
            and self.monto_total >= Decimal("0")
            and self.estado_reserva.strip()
        )

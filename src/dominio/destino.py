from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timezone
from typing import ClassVar


@dataclass
class Destino:
    id_destino: int | None = None
    nombre: str = ""
    pais: str = ""
    ciudad: str = ""
    descripcion: str = ""
    costo_base: Decimal = Decimal("0")
    disponible: bool = True
    fecha_creacion: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    tabla: ClassVar[str] = "destinos"
    clave_primaria: ClassVar[str] = "id_destino"

    def validar(self) -> bool:
        return bool(
            self.nombre.strip()
            and self.pais.strip()
            and self.ciudad.strip()
            and self.costo_base >= Decimal("0")
        )

    def eliminar_logico(self) -> None:
        self.disponible = False

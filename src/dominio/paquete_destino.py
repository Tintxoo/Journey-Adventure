from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar


@dataclass
class PaqueteDestino:
    id_paquete_destino: int | None = None
    id_paquete: int = 0
    id_destino: int = 0
    orden_itinerario: int = 0
    dias_estadia: int = 0
    costo_asignado: Decimal = Decimal("0")

    tabla: ClassVar[str] = "paquete_destinos"
    clave_primaria: ClassVar[str] = "id_paquete_destino"

    def validar(self) -> bool:
        return bool(
            self.id_paquete > 0
            and self.id_destino > 0
            and self.orden_itinerario > 0
            and self.dias_estadia > 0
            and self.costo_asignado >= Decimal("0")
        )

    def cambiar_orden(self, nuevo_orden: int) -> None:
        if nuevo_orden < 1:
            raise ValueError("El orden del itinerario debe ser mayor que cero.")
        self.orden_itinerario = nuevo_orden

    def recalcular_subtotal(self) -> Decimal:
        return self.costo_asignado * self.dias_estadia

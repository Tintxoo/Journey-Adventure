from datetime import date

from src.dominio import AvancePaquete, PaqueteTuristico
from .base_dao import BaseDAO


class PaqueteTuristicoDAO(BaseDAO[PaqueteTuristico]):
    entidad = PaqueteTuristico

    def obtener_avance(
        self,
        id_paquete: int,
        fecha_actual: date | None = None,
    ) -> AvancePaquete:
        return self._repositorio.obtener_avance_paquete(id_paquete, fecha_actual)

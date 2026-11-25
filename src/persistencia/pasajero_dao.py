from src.dominio import Pasajero
from .base_dao import BaseDAO


class PasajeroDAO(BaseDAO[Pasajero]):
    entidad = Pasajero

    def listar_por_reserva(self, id_reserva: int) -> list[Pasajero]:
        return self.listar_por(id_reserva=id_reserva)

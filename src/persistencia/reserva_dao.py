from src.dominio import Reserva
from .base_dao import BaseDAO


class ReservaDAO(BaseDAO[Reserva]):
    entidad = Reserva

    def listar_por_usuario(self, id_usuario: int) -> list[Reserva]:
        return self.listar_por(id_usuario=id_usuario)

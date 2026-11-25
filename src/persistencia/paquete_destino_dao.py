from src.dominio import PaqueteDestino
from .base_dao import BaseDAO


class PaqueteDestinoDAO(BaseDAO[PaqueteDestino]):
    entidad = PaqueteDestino

    def listar_por_paquete(self, id_paquete: int) -> list[PaqueteDestino]:
        return self.listar_por(id_paquete=id_paquete)

from src.dominio import ActividadPaquete
from .base_dao import BaseDAO


class ActividadPaqueteDAO(BaseDAO[ActividadPaquete]):
    entidad = ActividadPaquete

    def listar_por_paquete(self, id_paquete: int) -> list[ActividadPaquete]:
        return self._repositorio.listar_actividades_paquete(id_paquete)

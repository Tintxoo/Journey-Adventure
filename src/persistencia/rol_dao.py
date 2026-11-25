from src.dominio import Rol
from src.persistencia.repositorio_sqlite import RepositorioSQLite
from .base_dao import BaseDAO


class RolDAO(BaseDAO[Rol]):
    entidad = Rol

    def crear_predeterminados(self) -> list[Rol]:
        return self._repositorio.crear_roles_predeterminados()

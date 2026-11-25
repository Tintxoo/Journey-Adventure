from typing import Any, Generic, TypeVar

from src.dominio import (
    ActividadPaquete,
    Destino,
    PaqueteDestino,
    PaqueteTuristico,
    Pasajero,
    Reserva,
    Rol,
    Usuario,
)
from src.persistencia.repositorio_sqlite import RepositorioSQLite

EntidadDAO = TypeVar(
    "EntidadDAO",
    ActividadPaquete,
    Destino,
    PaqueteDestino,
    PaqueteTuristico,
    Pasajero,
    Reserva,
    Rol,
    Usuario,
)


class BaseDAO(Generic[EntidadDAO]):
    entidad: type[EntidadDAO]

    def __init__(self, repositorio: RepositorioSQLite) -> None:
        self._repositorio = repositorio

    def crear(self, entidad: EntidadDAO) -> EntidadDAO:
        return self._repositorio.crear(self._validar_entidad(entidad))

    def obtener_por_id(self, identificador: int) -> EntidadDAO | None:
        return self._repositorio.obtener(self.entidad, identificador)

    def listar(self) -> list[EntidadDAO]:
        return self._repositorio.listar(self.entidad)

    def listar_por(self, **filtros: Any) -> list[EntidadDAO]:
        return self._repositorio.listar_por(self.entidad, **filtros)

    def actualizar(self, entidad: EntidadDAO) -> EntidadDAO:
        return self._repositorio.actualizar(self._validar_entidad(entidad))

    def eliminar(self, identificador: int) -> bool:
        return self._repositorio.eliminar(self.entidad, identificador)

    def _validar_entidad(self, entidad: EntidadDAO) -> EntidadDAO:
        if type(entidad) is not self.entidad:
            raise TypeError(
                f"{type(self).__name__} solo acepta entidades "
                f"{self.entidad.__name__}."
            )
        return entidad

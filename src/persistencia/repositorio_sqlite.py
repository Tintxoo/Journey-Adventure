import sqlite3
from contextlib import contextmanager
from dataclasses import fields, replace
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from types import UnionType
from typing import Any, TypeVar, Union, get_args, get_origin, get_type_hints
from collections.abc import Iterator

from .crear_db import crear_base_datos
from src.dominio import (
    ActividadPaquete,
    AvancePaquete,
    Destino,
    PaqueteDestino,
    PaqueteTuristico,
    Pasajero,
    Reserva,
    Rol,
    Usuario,
)

Entidad = TypeVar(
    "Entidad",
    Rol,
    Usuario,
    Destino,
    PaqueteTuristico,
    PaqueteDestino,
    ActividadPaquete,
    Reserva,
    Pasajero,
)

_TIPOS_ENTIDAD = {
    Rol,
    Usuario,
    Destino,
    PaqueteTuristico,
    PaqueteDestino,
    ActividadPaquete,
    Reserva,
    Pasajero,
}


class RepositorioSQLite:
    """CRUD SQLite para las entidades del dominio del diagrama UML."""

    def __init__(self, ruta: str | Path = "data/journey_adventure.sqlite3") -> None:
        self._conexion = crear_base_datos(ruta)
        self._transaccion_activa = False

    def __enter__(self) -> "RepositorioSQLite":
        return self

    def __exit__(self, tipo_error: Any, error: Any, traceback: Any) -> None:
        self.cerrar()

    def cerrar(self) -> None:
        self._conexion.close()

    @contextmanager
    def transaccion(self) -> Iterator[None]:
        if self._transaccion_activa:
            raise RuntimeError("No se permiten transacciones anidadas.")
        self._conexion.execute("BEGIN")
        self._transaccion_activa = True
        try:
            yield
        except BaseException:
            self._conexion.rollback()
            raise
        else:
            self._conexion.commit()
        finally:
            self._transaccion_activa = False

    def crear(self, entidad: Entidad) -> Entidad:
        tipo = type(entidad)
        self._validar_tipo(tipo)
        self._validar_entidad(entidad)
        if isinstance(entidad, ActividadPaquete):
            self._validar_fecha_actividad(entidad)
        clave = tipo.clave_primaria
        if getattr(entidad, clave) is not None:
            raise ValueError(f"{clave} debe ser None al crear una entidad.")

        columnas = [campo.name for campo in fields(entidad) if campo.name != clave]
        valores = [self._codificar(getattr(entidad, columna)) for columna in columnas]
        placeholders = ", ".join("?" for _ in columnas)
        sql = (
            f"INSERT INTO {tipo.tabla} ({', '.join(columnas)}) "
            f"VALUES ({placeholders})"
        )
        cursor = self._conexion.execute(sql, valores)
        self._confirmar()
        return replace(entidad, **{clave: cursor.lastrowid})

    def obtener(self, tipo: type[Entidad], identificador: int) -> Entidad | None:
        self._validar_tipo(tipo)
        fila = self._conexion.execute(
            f"SELECT * FROM {tipo.tabla} WHERE {tipo.clave_primaria} = ?",
            (identificador,),
        ).fetchone()
        return self._desde_fila(tipo, fila) if fila is not None else None

    def listar(self, tipo: type[Entidad]) -> list[Entidad]:
        self._validar_tipo(tipo)
        filas = self._conexion.execute(
            f"SELECT * FROM {tipo.tabla} ORDER BY {tipo.clave_primaria}"
        ).fetchall()
        return [self._desde_fila(tipo, fila) for fila in filas]

    def listar_por(self, tipo: type[Entidad], **filtros: Any) -> list[Entidad]:
        self._validar_tipo(tipo)
        columnas = {campo.name for campo in fields(tipo)}
        columnas_desconocidas = filtros.keys() - columnas
        if columnas_desconocidas:
            raise ValueError(
                f"Filtros no válidos para {tipo.__name__}: "
                f"{', '.join(sorted(columnas_desconocidas))}."
            )

        condiciones = []
        valores = []
        for columna, valor in filtros.items():
            if valor is None:
                condiciones.append(f"{columna} IS NULL")
            else:
                condiciones.append(f"{columna} = ?")
                valores.append(self._codificar(valor))
        where = f" WHERE {' AND '.join(condiciones)}" if condiciones else ""
        filas = self._conexion.execute(
            f"SELECT * FROM {tipo.tabla}{where} "
            f"ORDER BY {tipo.clave_primaria}",
            valores,
        ).fetchall()
        return [self._desde_fila(tipo, fila) for fila in filas]

    def crear_roles_predeterminados(self) -> list[Rol]:
        roles_existentes: dict[str, Rol] = {}
        for rol in self.listar(Rol):
            roles_existentes.setdefault(rol.nombre_rol.strip().casefold(), rol)

        roles: list[Rol] = []
        for rol in Rol.roles_predeterminados():
            clave = rol.nombre_rol.casefold()
            roles.append(roles_existentes.get(clave) or self.crear(rol))
        return roles

    def obtener_avance_paquete(
        self,
        id_paquete: int,
        fecha_actual: date | None = None,
    ) -> AvancePaquete:
        paquete = self.obtener(PaqueteTuristico, id_paquete)
        if paquete is None:
            raise LookupError(f"No existe paquete con id_paquete={id_paquete}.")
        actividades = self.listar_actividades_paquete(id_paquete)
        return paquete.calcular_avance(actividades, fecha_actual)

    def actualizar(self, entidad: Entidad) -> Entidad:
        tipo = type(entidad)
        self._validar_tipo(tipo)
        self._validar_entidad(entidad)
        clave = tipo.clave_primaria
        identificador = getattr(entidad, clave)
        if identificador is None:
            raise ValueError(f"{clave} es necesario para actualizar una entidad.")
        if isinstance(entidad, PaqueteTuristico):
            actividades = self.listar_actividades_paquete(identificador)
            if any(
                not actividad.validar_para_paquete(
                    entidad.fecha_inicio, entidad.fecha_fin
                )
                for actividad in actividades
            ):
                raise ValueError(
                    "Las nuevas fechas del paquete dejan actividades fuera de su duración."
                )
        if isinstance(entidad, ActividadPaquete):
            self._validar_fecha_actividad(entidad)

        columnas = [campo.name for campo in fields(entidad) if campo.name != clave]
        asignaciones = ", ".join(f"{columna} = ?" for columna in columnas)
        valores = [self._codificar(getattr(entidad, columna)) for columna in columnas]
        valores.append(identificador)
        cursor = self._conexion.execute(
            f"UPDATE {tipo.tabla} SET {asignaciones} "
            f"WHERE {clave} = ?",
            valores,
        )
        if cursor.rowcount == 0:
            self._conexion.rollback()
            raise LookupError(f"No existe {tipo.__name__} con {clave}={identificador}.")
        self._confirmar()
        return entidad

    def eliminar(self, tipo: type[Entidad], identificador: int) -> bool:
        self._validar_tipo(tipo)
        if tipo is Destino:
            cursor = self._conexion.execute(
                "UPDATE destinos SET disponible = 0 WHERE id_destino = ?",
                (identificador,),
            )
        else:
            cursor = self._conexion.execute(
                f"DELETE FROM {tipo.tabla} WHERE {tipo.clave_primaria} = ?",
                (identificador,),
            )
        self._confirmar()
        return cursor.rowcount > 0

    @staticmethod
    def _validar_tipo(tipo: type[Any]) -> None:
        if tipo not in _TIPOS_ENTIDAD:
            raise TypeError(f"Tipo de entidad no soportado: {tipo.__name__}.")

    def _confirmar(self) -> None:
        if not self._transaccion_activa:
            self._conexion.commit()

    @staticmethod
    def _validar_entidad(entidad: Entidad) -> None:
        validar = getattr(entidad, "validar", None)
        if validar is None:
            validar = getattr(entidad, "validar_datos", None)
        if validar is not None and not validar():
            raise ValueError(f"Los datos de {type(entidad).__name__} no son válidos.")

    def _validar_fecha_actividad(self, actividad: ActividadPaquete) -> None:
        paquete = self.obtener(PaqueteTuristico, actividad.id_paquete)
        if paquete is not None and not actividad.validar_para_paquete(
            paquete.fecha_inicio, paquete.fecha_fin
        ):
            raise ValueError("La actividad está fuera de las fechas del paquete.")

    def listar_actividades_paquete(self, id_paquete: int) -> list[ActividadPaquete]:
        return self.listar_por(ActividadPaquete, id_paquete=id_paquete)

    @staticmethod
    def _codificar(valor: Any) -> Any:
        if isinstance(valor, bool):
            return int(valor)
        if isinstance(valor, Decimal):
            return str(valor)
        if isinstance(valor, (datetime, date)):
            return valor.isoformat()
        return valor

    @staticmethod
    def _desde_fila(tipo: type[Entidad], fila: sqlite3.Row) -> Entidad:
        anotaciones = get_type_hints(tipo)
        valores = {
            campo.name: RepositorioSQLite._decodificar(
                fila[campo.name], anotaciones[campo.name]
            )
            for campo in fields(tipo)
        }
        return tipo(**valores)

    @staticmethod
    def _decodificar(valor: Any, tipo: Any) -> Any:
        if valor is None:
            return None
        origen = get_origin(tipo)
        if origen in (Union, UnionType):
            tipos = [opcion for opcion in get_args(tipo) if opcion is not type(None)]
            if len(tipos) == 1:
                return RepositorioSQLite._decodificar(valor, tipos[0])
        if tipo is bool:
            return bool(valor)
        if tipo is Decimal:
            return Decimal(valor)
        if tipo is datetime:
            return datetime.fromisoformat(valor)
        if tipo is date:
            return date.fromisoformat(valor)
        return valor

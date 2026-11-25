from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import ClassVar, Iterable

from .actividad_paquete import (
    ActividadPaquete,
    ActividadProgramada,
    AvancePaquete,
    EstadoActividad,
)


@dataclass
class PaqueteTuristico:
    id_paquete: int | None = None
    nombre_paquete: str = ""
    descripcion: str = ""
    fecha_inicio: date = field(default_factory=date.today)
    fecha_fin: date = field(default_factory=date.today)
    costo_total: Decimal = Decimal("0")
    cupos_totales: int = 0
    cupos_disponibles: int = 0
    estado: str = "disponible"

    tabla: ClassVar[str] = "paquetes_turisticos"
    clave_primaria: ClassVar[str] = "id_paquete"

    def verificar_disponibilidad(self, personas: int) -> bool:
        return personas > 0 and self.cupos_disponibles >= personas

    def validar(self) -> bool:
        return bool(
            self.nombre_paquete.strip()
            and self.fecha_fin >= self.fecha_inicio
            and self.costo_total >= Decimal("0")
            and 0 <= self.cupos_disponibles <= self.cupos_totales
        )

    def descontar_cupos(self, personas: int) -> None:
        if not self.verificar_disponibilidad(personas):
            raise ValueError("No hay suficientes cupos disponibles.")
        self.cupos_disponibles -= personas

    def calcular_avance(
        self,
        actividades: Iterable[ActividadPaquete],
        fecha_actual: date | None = None,
    ) -> AvancePaquete:
        hoy = fecha_actual or date.today()
        programadas: list[ActividadProgramada] = []
        for actividad in actividades:
            if self.id_paquete is not None and actividad.id_paquete != self.id_paquete:
                raise ValueError("La actividad no pertenece a este paquete.")
            if not actividad.validar_para_paquete(self.fecha_inicio, self.fecha_fin):
                raise ValueError("La actividad está fuera de las fechas del paquete.")
            fecha = actividad.fecha_programada(self.fecha_inicio)
            if fecha < hoy:
                estado = EstadoActividad.REALIZADA
            elif fecha == hoy:
                estado = EstadoActividad.EN_CURSO
            else:
                estado = EstadoActividad.PENDIENTE
            programadas.append(ActividadProgramada(actividad, fecha, estado))

        programadas.sort(
            key=lambda actividad: (
                actividad.fecha_programada,
                actividad.actividad.id_actividad or 0,
            )
        )
        realizadas = sum(
            actividad.estado is EstadoActividad.REALIZADA
            for actividad in programadas
        )
        porcentaje = 100 * realizadas / len(programadas) if programadas else 0.0
        actividades_iniciadas = [
            actividad for actividad in programadas if actividad.fecha_programada <= hoy
        ]
        if actividades_iniciadas:
            fecha_etapa = actividades_iniciadas[-1].fecha_programada
            etapa_actual = tuple(
                actividad
                for actividad in actividades_iniciadas
                if actividad.fecha_programada == fecha_etapa
            )
        else:
            etapa_actual = ()
        proxima = next(
            (
                actividad
                for actividad in programadas
                if actividad.estado is EstadoActividad.PENDIENTE
            ),
            None,
        )
        return AvancePaquete(porcentaje, tuple(programadas), etapa_actual, proxima)

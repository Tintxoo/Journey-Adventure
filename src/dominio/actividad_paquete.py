from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum
from typing import ClassVar


class EstadoActividad(str, Enum):
    PENDIENTE = "pendiente"
    EN_CURSO = "en_curso"
    REALIZADA = "realizada"


@dataclass
class ActividadPaquete:
    id_actividad: int | None = None
    id_paquete: int = 0
    nombre: str = ""
    descripcion: str = ""
    dia_relativo: int = 1

    tabla: ClassVar[str] = "actividades_paquete"
    clave_primaria: ClassVar[str] = "id_actividad"

    def validar(self) -> bool:
        return bool(
            self.id_paquete > 0
            and self.nombre.strip()
            and isinstance(self.dia_relativo, int)
            and not isinstance(self.dia_relativo, bool)
            and self.dia_relativo > 0
        )

    def validar_para_paquete(self, fecha_inicio: date, fecha_fin: date) -> bool:
        duracion_en_dias = (fecha_fin - fecha_inicio).days + 1
        return 1 <= self.dia_relativo <= duracion_en_dias

    def fecha_programada(self, fecha_inicio: date) -> date:
        if self.dia_relativo < 1:
            raise ValueError("El día relativo debe ser mayor o igual a 1.")
        return fecha_inicio + timedelta(days=self.dia_relativo - 1)


@dataclass(frozen=True)
class ActividadProgramada:
    actividad: ActividadPaquete
    fecha_programada: date
    estado: EstadoActividad


@dataclass(frozen=True)
class AvancePaquete:
    porcentaje_completado: float
    actividades: tuple[ActividadProgramada, ...]
    etapa_actual: tuple[ActividadProgramada, ...]
    proxima_actividad: ActividadProgramada | None

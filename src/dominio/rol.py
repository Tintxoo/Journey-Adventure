from dataclasses import dataclass
from typing import ClassVar


_PERMISOS_POR_ROL: dict[str, tuple[str, ...]] = {
    "cliente": (
        "usuario.registrarse",
        "usuario.autenticar",
        "destino.listar",
        "paquete.consultar_disponibilidad",
        "paquete.consultar_avance",
        "reserva.crear",
        "reserva.consultar_historial_propio",
        "pasajero.consultar_de_reserva_propia",
    ),
    "administrador": (
        "usuario.autenticar",
        "destino.crear",
        "destino.modificar",
        "destino.eliminar",
        "destino.listar",
        "paquete.crear",
        "paquete.consultar_disponibilidad",
    ),
}


@dataclass
class Rol:
    id_rol: int | None = None
    nombre_rol: str = ""
    descripcion: str = ""

    tabla: ClassVar[str] = "roles"
    clave_primaria: ClassVar[str] = "id_rol"

    def validar(self) -> bool:
        return bool(self.nombre_rol.strip())

    def obtener_permisos(self) -> list[str]:
        return list(_PERMISOS_POR_ROL.get(self.nombre_rol.strip().casefold(), ()))

    def tiene_permiso(self, permiso: str) -> bool:
        return permiso in self.obtener_permisos()

    @classmethod
    def roles_predeterminados(cls) -> tuple["Rol", ...]:
        return (
            cls(
                nombre_rol="Cliente",
                descripcion="Consulta opciones y administra sus propias reservas.",
            ),
            cls(
                nombre_rol="Administrador",
                descripcion="Gestiona destinos y paquetes turísticos.",
            ),
        )

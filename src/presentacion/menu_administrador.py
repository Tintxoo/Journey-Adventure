from decimal import Decimal
from collections.abc import Callable

from src.dominio import ActividadPaquete, Destino, PaqueteDestino, PaqueteTuristico
from src.persistencia import (
    ActividadPaqueteDAO,
    DestinoDAO,
    PaqueteDestinoDAO,
    PaqueteTuristicoDAO,
    RepositorioSQLite,
)
from .menu_base import (
    ejecutar_accion,
    limpiar_terminal,
    mostrar_entidades,
    pausar,
    pedir_booleano,
    pedir_decimal,
    pedir_entero,
    pedir_fecha,
    pedir_texto,
)


class MenuAdministrador:
    def __init__(self, repositorio: RepositorioSQLite) -> None:
        self.destinos = DestinoDAO(repositorio)
        self.paquetes = PaqueteTuristicoDAO(repositorio)
        self.paquete_destinos = PaqueteDestinoDAO(repositorio)
        self.actividades = ActividadPaqueteDAO(repositorio)

    def ejecutar(self) -> None:
        while True:
            limpiar_terminal()
            print("\n--- Menú Administrador ---")
            print("1. Gestionar destinos")
            print("2. Gestionar paquetes")
            print("0. Volver al menú principal")
            opcion = input("Selecciona una opción: ").strip()
            if opcion == "1":
                self._menu_destinos()
            elif opcion == "2":
                self._menu_paquetes()
            elif opcion == "0":
                return
            else:
                print("Opción no válida.")
                pausar()

    def _menu_destinos(self) -> None:
        acciones = {
            "1": ("Listar destinos", self._listar_destinos),
            "2": ("Crear destino", self._crear_destino),
            "3": ("Actualizar destino", self._actualizar_destino),
            "4": ("Desactivar destino", self._eliminar_destino),
        }
        self._menu_operaciones("Destinos", acciones)

    def _menu_paquetes(self) -> None:
        acciones = {
            "1": ("Listar paquetes", self._listar_paquetes),
            "2": ("Crear paquete", self._crear_paquete),
            "3": ("Actualizar paquete", self._actualizar_paquete),
            "4": ("Eliminar paquete", self._eliminar_paquete),
            "5": ("Agregar destino a paquete", self._agregar_destino),
            "6": ("Agregar actividad", self._agregar_actividad),
            "7": ("Consultar avance", self._consultar_avance),
        }
        self._menu_operaciones("Paquetes e itinerarios", acciones)

    def _menu_operaciones(
        self,
        titulo: str,
        acciones: dict[str, tuple[str, Callable[[], None]]],
    ) -> None:
        while True:
            limpiar_terminal()
            print(f"\n--- {titulo} ---")
            for opcion, (etiqueta, _) in acciones.items():
                print(f"{opcion}. {etiqueta}")
            print("0. Volver")
            opcion = input("Selecciona una opción: ").strip()
            if opcion == "0":
                return
            accion = acciones.get(opcion)
            if accion is None:
                print("Opción no válida.")
                pausar()
            else:
                ejecutar_accion(accion[1])
                pausar()

    def _listar_destinos(self) -> None:
        mostrar_entidades(self.destinos.listar())

    def _crear_destino(self) -> None:
        destino = Destino(
            nombre=pedir_texto("Nombre"),
            pais=pedir_texto("País"),
            ciudad=pedir_texto("Ciudad"),
            descripcion=pedir_texto("Descripción", ""),
            costo_base=pedir_decimal("Costo base", Decimal("0")),
        )
        creado = self.destinos.crear(destino)
        print(f"Destino creado con ID {creado.id_destino}.")

    def _actualizar_destino(self) -> None:
        identificador = pedir_entero("ID del destino", minimo=1)
        destino = self.destinos.obtener_por_id(identificador)
        if destino is None:
            raise LookupError(f"No existe destino con ID {identificador}.")
        destino.nombre = pedir_texto("Nombre", destino.nombre)
        destino.pais = pedir_texto("País", destino.pais)
        destino.ciudad = pedir_texto("Ciudad", destino.ciudad)
        destino.descripcion = pedir_texto("Descripción", destino.descripcion)
        destino.costo_base = pedir_decimal("Costo base", destino.costo_base)
        destino.disponible = pedir_booleano("Disponible", destino.disponible)
        self.destinos.actualizar(destino)
        print("Destino actualizado.")

    def _eliminar_destino(self) -> None:
        identificador = pedir_entero("ID del destino", minimo=1)
        if self.destinos.eliminar(identificador):
            print("Destino desactivado.")
        else:
            print("No se encontró el destino.")

    def _listar_paquetes(self) -> None:
        mostrar_entidades(self.paquetes.listar())

    def _crear_paquete(self) -> None:
        cupos = pedir_entero("Cupos totales", minimo=0)
        paquete = PaqueteTuristico(
            nombre_paquete=pedir_texto("Nombre del paquete"),
            descripcion=pedir_texto("Descripción", ""),
            fecha_inicio=pedir_fecha("Fecha de inicio"),
            fecha_fin=pedir_fecha("Fecha de término"),
            costo_total=pedir_decimal("Costo total"),
            cupos_totales=cupos,
            cupos_disponibles=cupos,
            estado=pedir_texto("Estado", "disponible"),
        )
        creado = self.paquetes.crear(paquete)
        print(f"Paquete creado con ID {creado.id_paquete}.")

    def _actualizar_paquete(self) -> None:
        identificador = pedir_entero("ID del paquete", minimo=1)
        paquete = self.paquetes.obtener_por_id(identificador)
        if paquete is None:
            raise LookupError(f"No existe paquete con ID {identificador}.")
        paquete.nombre_paquete = pedir_texto("Nombre", paquete.nombre_paquete)
        paquete.descripcion = pedir_texto("Descripción", paquete.descripcion)
        paquete.fecha_inicio = pedir_fecha("Fecha de inicio", paquete.fecha_inicio)
        paquete.fecha_fin = pedir_fecha("Fecha de término", paquete.fecha_fin)
        paquete.costo_total = pedir_decimal("Costo total", paquete.costo_total)
        paquete.cupos_totales = pedir_entero(
            "Cupos totales", paquete.cupos_totales, minimo=0
        )
        paquete.cupos_disponibles = pedir_entero(
            "Cupos disponibles", paquete.cupos_disponibles, minimo=0
        )
        paquete.estado = pedir_texto("Estado", paquete.estado)
        self.paquetes.actualizar(paquete)
        print("Paquete actualizado.")

    def _eliminar_paquete(self) -> None:
        identificador = pedir_entero("ID del paquete", minimo=1)
        if self.paquetes.eliminar(identificador):
            print("Paquete eliminado.")
        else:
            print("No se encontró el paquete.")

    def _agregar_destino(self) -> None:
        asignacion = PaqueteDestino(
            id_paquete=pedir_entero("ID del paquete", minimo=1),
            id_destino=pedir_entero("ID del destino", minimo=1),
            orden_itinerario=pedir_entero("Orden en el itinerario", minimo=1),
            dias_estadia=pedir_entero("Días de estadía", minimo=1),
            costo_asignado=pedir_decimal("Costo asignado", Decimal("0")),
        )
        creado = self.paquete_destinos.crear(asignacion)
        print(f"Destino agregado al paquete (ID {creado.id_paquete_destino}).")

    def _agregar_actividad(self) -> None:
        actividad = ActividadPaquete(
            id_paquete=pedir_entero("ID del paquete", minimo=1),
            nombre=pedir_texto("Nombre de la actividad"),
            descripcion=pedir_texto("Descripción", ""),
            dia_relativo=pedir_entero("Día relativo al inicio", minimo=1),
        )
        creado = self.actividades.crear(actividad)
        print(f"Actividad creada con ID {creado.id_actividad}.")

    def _consultar_avance(self) -> None:
        identificador = pedir_entero("ID del paquete", minimo=1)
        avance = self.paquetes.obtener_avance(identificador)
        print(f"Avance: {avance.porcentaje_completado:.1f}%")
        print("Etapa actual:")
        mostrar_entidades([actividad.actividad for actividad in avance.etapa_actual])
        print("Próxima actividad:")
        if avance.proxima_actividad is None:
            print("No hay actividades pendientes.")
        else:
            mostrar_entidades([avance.proxima_actividad.actividad])
        print("Actividades:")
        for programada in avance.actividades:
            print(
                f"{programada.fecha_programada} - "
                f"{programada.actividad.nombre}: {programada.estado.value}"
            )

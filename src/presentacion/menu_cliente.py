from datetime import date
from decimal import Decimal
from uuid import uuid4

from src.dominio import Pasajero, Reserva, Usuario
from src.persistencia import (
    DestinoDAO,
    PaqueteTuristicoDAO,
    PasajeroDAO,
    ReservaDAO,
    RolDAO,
    RepositorioSQLite,
    UsuarioDAO,
)
from .menu_base import (
    ejecutar_accion,
    limpiar_terminal,
    mostrar_entidades,
    pausar,
    pedir_entero,
    pedir_fecha,
    pedir_texto,
)


class MenuCliente:
    def __init__(self, repositorio: RepositorioSQLite) -> None:
        self.repositorio = repositorio
        self.destinos = DestinoDAO(repositorio)
        self.paquetes = PaqueteTuristicoDAO(repositorio)
        self.reservas = ReservaDAO(repositorio)
        self.pasajeros = PasajeroDAO(repositorio)
        self.usuarios = UsuarioDAO(repositorio)
        self.roles = RolDAO(repositorio)
        self.usuario_actual: Usuario | None = None

    def ejecutar(self) -> None:
        acciones = {
            "1": ("Registrar cliente", self._registrar_cliente),
            "2": ("Seleccionar cliente por ID", self._seleccionar_cliente),
            "3": ("Consultar destinos", self._listar_destinos),
            "4": ("Consultar paquetes", self._listar_paquetes),
            "5": ("Ver avance de paquete", self._consultar_avance),
            "6": ("Crear reserva", self._crear_reserva),
            "7": ("Ver historial de reservas", self._listar_reservas),
            "8": ("Ver pasajeros de una reserva", self._listar_pasajeros),
        }
        while True:
            limpiar_terminal()
            print("\n--- Menú Cliente ---")
            if self.usuario_actual is None:
                print("Cliente activo: ninguno")
            else:
                print(f"Cliente activo: {self.usuario_actual.nombre_completo}")
            for opcion, (etiqueta, _) in acciones.items():
                print(f"{opcion}. {etiqueta}")
            print("0. Volver al menú principal")
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

    def _registrar_cliente(self) -> None:
        roles = self.roles.crear_predeterminados()
        rol_cliente = next(rol for rol in roles if rol.nombre_rol.casefold() == "cliente")
        contrasena = pedir_texto("Contraseña (mínimo 8 caracteres)")
        usuario = Usuario(
            id_rol=rol_cliente.id_rol,
            nombre_completo=pedir_texto("Nombre completo"),
            email=pedir_texto("Correo electrónico"),
            password_hash=Usuario.crear_password_hash(contrasena),
            documento_identidad=pedir_texto("Documento de identidad"),
            telefono=pedir_texto("Teléfono", ""),
        )
        self.usuario_actual = self.usuarios.crear(usuario)
        print(f"Cliente registrado con ID {self.usuario_actual.id_usuario}.")

    def _seleccionar_cliente(self) -> None:
        identificador = pedir_entero("ID del cliente", minimo=1)
        usuario = self.usuarios.obtener_por_id(identificador)
        if usuario is None:
            raise LookupError(f"No existe cliente con ID {identificador}.")
        self.usuario_actual = usuario
        print(f"Cliente activo: {usuario.nombre_completo}.")

    def _listar_destinos(self) -> None:
        disponibles = [destino for destino in self.destinos.listar() if destino.disponible]
        mostrar_entidades(disponibles)

    def _listar_paquetes(self) -> None:
        paquetes = [
            paquete
            for paquete in self.paquetes.listar()
            if paquete.estado.casefold() == "disponible"
            and paquete.cupos_disponibles > 0
            and paquete.fecha_fin >= date.today()
        ]
        mostrar_entidades(paquetes)

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
        for programada in avance.actividades:
            print(
                f"{programada.fecha_programada} - "
                f"{programada.actividad.nombre}: {programada.estado.value}"
            )

    def _crear_reserva(self) -> None:
        if self.usuario_actual is None:
            raise ValueError("Registra o selecciona un cliente antes de reservar.")
        id_paquete = pedir_entero("ID del paquete", minimo=1)
        paquete = self.paquetes.obtener_por_id(id_paquete)
        if paquete is None:
            raise LookupError(f"No existe paquete con ID {id_paquete}.")
        cantidad = pedir_entero("Cantidad de personas", minimo=1)
        if paquete.estado.casefold() != "disponible" or not paquete.verificar_disponibilidad(cantidad):
            raise ValueError("El paquete no tiene suficientes cupos disponibles.")

        datos_pasajeros = []
        for numero in range(cantidad):
            print(f"Datos del pasajero {numero + 1}:")
            datos_pasajeros.append(
                {
                    "nombre_completo": pedir_texto("Nombre completo"),
                    "documento_identidad": pedir_texto("Documento de identidad"),
                    "fecha_nacimiento": pedir_fecha("Fecha de nacimiento"),
                    "telefono_contacto": pedir_texto("Teléfono de contacto", ""),
                }
            )

        reserva = Reserva(
            codigo_reserva=uuid4().hex[:12].upper(),
            id_usuario=self.usuario_actual.id_usuario,
            id_paquete=id_paquete,
            cantidad_personas=cantidad,
            monto_total=paquete.costo_total * cantidad,
            estado_reserva="confirmada",
        )
        with self.repositorio.transaccion():
            creada = self.reservas.crear(reserva)
            paquete.descontar_cupos(cantidad)
            self.paquetes.actualizar(paquete)
            for numero, datos in enumerate(datos_pasajeros):
                self.pasajeros.crear(
                    Pasajero(
                        id_reserva=creada.id_reserva,
                        **datos,
                        es_titular=numero == 0,
                    )
                )
        print(f"Reserva confirmada. Código: {creada.codigo_reserva}.")

    def _listar_reservas(self) -> None:
        if self.usuario_actual is None:
            raise ValueError("Registra o selecciona un cliente primero.")
        mostrar_entidades(
            self.reservas.listar_por_usuario(self.usuario_actual.id_usuario)
        )

    def _listar_pasajeros(self) -> None:
        id_reserva = pedir_entero("ID de la reserva", minimo=1)
        mostrar_entidades(self.pasajeros.listar_por_reserva(id_reserva))

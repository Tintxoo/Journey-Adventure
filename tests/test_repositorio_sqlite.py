import unittest
from datetime import date, datetime, timezone
from dataclasses import replace
from decimal import Decimal
import sqlite3
import tempfile
from pathlib import Path

from src.dominio import (
    ActividadPaquete,
    Destino,
    EstadoActividad,
    PaqueteDestino,
    PaqueteTuristico,
    Pasajero,
    Reserva,
    Rol,
    Usuario,
)
from src.persistencia import (
    ActividadPaqueteDAO,
    DestinoDAO,
    PaqueteDestinoDAO,
    PaqueteTuristicoDAO,
    PasajeroDAO,
    RepositorioSQLite,
    ReservaDAO,
    RolDAO,
    UsuarioDAO,
    crear_base_datos,
)


class RepositorioSQLiteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repositorio = RepositorioSQLite(":memory:")

    def tearDown(self) -> None:
        self.repositorio.cerrar()

    def test_crud_de_entidades_y_conversion_de_tipos(self) -> None:
        rol = self.repositorio.crear(Rol(nombre_rol="Cliente", descripcion="Usuario"))
        usuario = self.repositorio.crear(
            Usuario(
                id_rol=rol.id_rol,
                nombre_completo="Ana Pérez",
                email="ana@example.com",
                password_hash="hash",
                documento_identidad="DOC-1",
                telefono="555-123",
                fecha_registro=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        )
        destino = self.repositorio.crear(
            Destino(
                nombre="Montaña",
                pais="Chile",
                ciudad="Santiago",
                costo_base=Decimal("125.50"),
                fecha_creacion=datetime(2026, 1, 2, tzinfo=timezone.utc),
            )
        )
        paquete = self.repositorio.crear(
            PaqueteTuristico(
                nombre_paquete="Andes",
                fecha_inicio=date(2026, 2, 1),
                fecha_fin=date(2026, 2, 5),
                costo_total=Decimal("500.00"),
                cupos_totales=4,
                cupos_disponibles=4,
            )
        )
        paquete_destino = self.repositorio.crear(
            PaqueteDestino(
                id_paquete=paquete.id_paquete,
                id_destino=destino.id_destino,
                orden_itinerario=1,
                dias_estadia=4,
                costo_asignado=Decimal("125.50"),
            )
        )
        reserva = self.repositorio.crear(
            Reserva(
                codigo_reserva="RES-1",
                id_usuario=usuario.id_usuario,
                id_paquete=paquete.id_paquete,
                fecha_reserva=datetime(2026, 1, 3, tzinfo=timezone.utc),
                cantidad_personas=1,
                monto_total=Decimal("500.00"),
                observaciones=None,
            )
        )
        pasajero = self.repositorio.crear(
            Pasajero(
                id_reserva=reserva.id_reserva,
                nombre_completo="Ana Pérez",
                documento_identidad="DOC-1",
                fecha_nacimiento=date(1990, 6, 15),
                telefono_contacto="555-123",
                es_titular=True,
            )
        )

        self.assertEqual(self.repositorio.obtener(Rol, rol.id_rol), rol)
        self.assertTrue(self.repositorio.obtener(Usuario, usuario.id_usuario).activo)
        self.assertEqual(
            self.repositorio.obtener(Destino, destino.id_destino).costo_base,
            Decimal("125.50"),
        )
        self.assertEqual(
            self.repositorio.obtener(PaqueteTuristico, paquete.id_paquete).fecha_inicio,
            date(2026, 2, 1),
        )
        self.assertEqual(
            self.repositorio.obtener(PaqueteDestino, paquete_destino.id_paquete_destino),
            paquete_destino,
        )
        self.assertEqual(
            self.repositorio.obtener(Reserva, reserva.id_reserva).observaciones, None
        )
        self.assertTrue(
            self.repositorio.obtener(Pasajero, pasajero.id_pasajero).es_titular
        )

        actualizado = self.repositorio.actualizar(replace(destino, nombre="Cordillera"))
        self.assertEqual(actualizado.nombre, "Cordillera")
        self.assertEqual(self.repositorio.listar(Destino)[0].nombre, "Cordillera")
        self.assertTrue(self.repositorio.eliminar(Pasajero, pasajero.id_pasajero))
        self.assertIsNone(self.repositorio.obtener(Pasajero, pasajero.id_pasajero))

    def test_avance_se_calcula_desde_dias_relativos_del_paquete(self) -> None:
        paquete = self.repositorio.crear(
            PaqueteTuristico(
                nombre_paquete="Cordillera",
                fecha_inicio=date(2026, 8, 10),
                fecha_fin=date(2026, 8, 12),
                costo_total=Decimal("300"),
                cupos_totales=5,
                cupos_disponibles=5,
            )
        )
        primera = self.repositorio.crear(
            ActividadPaquete(
                id_paquete=paquete.id_paquete,
                nombre="Llegada",
                dia_relativo=1,
            )
        )
        segunda = self.repositorio.crear(
            ActividadPaquete(
                id_paquete=paquete.id_paquete,
                nombre="Excursion",
                dia_relativo=2,
            )
        )
        tercera = self.repositorio.crear(
            ActividadPaquete(
                id_paquete=paquete.id_paquete,
                nombre="Regreso",
                dia_relativo=3,
            )
        )
        with self.assertRaises(ValueError):
            self.repositorio.crear(
                ActividadPaquete(
                    id_paquete=paquete.id_paquete,
                    nombre="Día fraccionario",
                    dia_relativo=1.5,
                )
            )

        avance = self.repositorio.obtener_avance_paquete(
            paquete.id_paquete, date(2026, 8, 11)
        )
        self.assertEqual(avance.porcentaje_completado, 100 / 3)
        self.assertEqual(
            [actividad.estado for actividad in avance.actividades],
            [
                EstadoActividad.REALIZADA,
                EstadoActividad.EN_CURSO,
                EstadoActividad.PENDIENTE,
            ],
        )
        self.assertEqual(avance.etapa_actual[0].actividad, segunda)
        self.assertEqual(avance.proxima_actividad.actividad, tercera)

        antes_del_inicio = self.repositorio.obtener_avance_paquete(
            paquete.id_paquete, date(2026, 8, 9)
        )
        self.assertEqual(antes_del_inicio.porcentaje_completado, 0)
        self.assertEqual(antes_del_inicio.etapa_actual, ())
        self.assertEqual(antes_del_inicio.proxima_actividad.actividad, primera)

        despues_del_paquete = self.repositorio.obtener_avance_paquete(
            paquete.id_paquete, date(2026, 8, 13)
        )
        self.assertEqual(despues_del_paquete.porcentaje_completado, 100)
        self.assertEqual(despues_del_paquete.etapa_actual[0].actividad, tercera)
        self.assertIsNone(despues_del_paquete.proxima_actividad)

    def test_daos_tipados_delegan_en_el_crud_general(self) -> None:
        rol_dao = RolDAO(self.repositorio)
        usuario_dao = UsuarioDAO(self.repositorio)
        destino_dao = DestinoDAO(self.repositorio)
        paquete_dao = PaqueteTuristicoDAO(self.repositorio)
        paquete_destino_dao = PaqueteDestinoDAO(self.repositorio)
        actividad_dao = ActividadPaqueteDAO(self.repositorio)
        reserva_dao = ReservaDAO(self.repositorio)
        pasajero_dao = PasajeroDAO(self.repositorio)

        rol = Rol(nombre_rol="Cliente")
        rol = rol_dao.crear(rol)
        usuario = usuario_dao.crear(
            Usuario(
                id_rol=rol.id_rol,
                nombre_completo="Ana",
                email="ana@example.com",
                password_hash="hash",
                documento_identidad="DOC-DAO",
            )
        )
        destino = destino_dao.crear(
            Destino(nombre="Lago", pais="Chile", ciudad="Pucón")
        )
        paquete = paquete_dao.crear(
            PaqueteTuristico(
                nombre_paquete="Sur",
                fecha_inicio=date(2026, 10, 1),
                fecha_fin=date(2026, 10, 2),
                costo_total=Decimal("100"),
                cupos_totales=4,
                cupos_disponibles=4,
            )
        )
        paquete_destino = paquete_destino_dao.crear(
            PaqueteDestino(
                id_paquete=paquete.id_paquete,
                id_destino=destino.id_destino,
                orden_itinerario=1,
                dias_estadia=2,
            )
        )
        actividad = actividad_dao.crear(
            ActividadPaquete(
                id_paquete=paquete.id_paquete,
                nombre="Visita",
                dia_relativo=2,
            )
        )
        reserva = reserva_dao.crear(
            Reserva(
                codigo_reserva="DAO-1",
                id_usuario=usuario.id_usuario,
                id_paquete=paquete.id_paquete,
            )
        )
        pasajero = pasajero_dao.crear(
            Pasajero(
                id_reserva=reserva.id_reserva,
                nombre_completo="Ana",
                documento_identidad="DOC-DAO",
                fecha_nacimiento=date(1990, 1, 1),
            )
        )

        registros = [
            (rol_dao, rol),
            (usuario_dao, usuario),
            (destino_dao, destino),
            (paquete_dao, paquete),
            (paquete_destino_dao, paquete_destino),
            (actividad_dao, actividad),
            (reserva_dao, reserva),
            (pasajero_dao, pasajero),
        ]
        for dao, entidad in registros:
            id_entidad = getattr(entidad, dao.entidad.clave_primaria)
            self.assertEqual(dao.obtener_por_id(id_entidad), entidad)
            self.assertIn(entidad, dao.listar())
            self.assertEqual(dao.actualizar(entidad), entidad)

        self.assertEqual(
            paquete_destino_dao.listar_por_paquete(paquete.id_paquete),
            [paquete_destino],
        )
        self.assertEqual(
            actividad_dao.listar_por_paquete(paquete.id_paquete), [actividad]
        )
        self.assertEqual(
            reserva_dao.listar_por_usuario(usuario.id_usuario), [reserva]
        )
        self.assertEqual(
            pasajero_dao.listar_por_reserva(reserva.id_reserva), [pasajero]
        )
        self.assertEqual(
            paquete_dao.obtener_avance(paquete.id_paquete, date(2026, 10, 2))
            .etapa_actual[0]
            .actividad,
            actividad,
        )
        with self.assertRaises(ValueError):
            usuario_dao.listar_por(columna_inexistente="x")
        with self.assertRaises(TypeError):
            usuario_dao.crear(Rol(nombre_rol="Administrador"))

        for dao, entidad in reversed(registros):
            id_entidad = getattr(entidad, dao.entidad.clave_primaria)
            self.assertTrue(dao.eliminar(id_entidad))

    def test_actividades_deben_estar_dentro_de_la_duracion_del_paquete(self) -> None:
        paquete = self.repositorio.crear(
            PaqueteTuristico(
                nombre_paquete="Costa",
                fecha_inicio=date(2026, 9, 1),
                fecha_fin=date(2026, 9, 2),
                costo_total=Decimal("200"),
                cupos_totales=2,
                cupos_disponibles=2,
            )
        )
        with self.assertRaises(ValueError):
            self.repositorio.crear(
                ActividadPaquete(
                    id_paquete=paquete.id_paquete,
                    nombre="Actividad fuera de fechas",
                    dia_relativo=3,
                )
            )

        actividad = self.repositorio.crear(
            ActividadPaquete(
                id_paquete=paquete.id_paquete,
                nombre="Visita",
                dia_relativo=2,
            )
        )
        with self.assertRaises(ValueError):
            self.repositorio.actualizar(
                replace(paquete, fecha_fin=date(2026, 9, 1))
            )
        self.assertEqual(
            self.repositorio.obtener(ActividadPaquete, actividad.id_actividad),
            actividad,
        )

    def test_claves_foraneas_y_eliminacion_logica_de_destino(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.repositorio.crear(
                Usuario(
                    id_rol=999,
                    nombre_completo="Ana",
                    email="ana@example.com",
                    password_hash="hash",
                    documento_identidad="DOC-1",
                )
            )

        destino = self.repositorio.crear(
            Destino(nombre="Lago", pais="Chile", ciudad="Pucón")
        )
        self.assertTrue(self.repositorio.eliminar(Destino, destino.id_destino))
        self.assertFalse(
            self.repositorio.obtener(Destino, destino.id_destino).disponible
        )
        self.assertFalse(self.repositorio.eliminar(Destino, -1))

    def test_rechaza_entidades_invalidas(self) -> None:
        with self.assertRaises(ValueError):
            self.repositorio.crear(Rol(nombre_rol=" "))

        with self.assertRaises(ValueError):
            self.repositorio.crear(
                Usuario(
                    id_rol=1,
                    nombre_completo="Ana",
                    email="correo-invalido",
                    password_hash="hash",
                    documento_identidad="DOC-1",
                )
            )

    def test_crea_roles_predeterminados_con_permisos_idempotentemente(self) -> None:
        roles = RolDAO(self.repositorio).crear_predeterminados()
        cliente, administrador = roles

        self.assertEqual(cliente.nombre_rol, "Cliente")
        self.assertTrue(cliente.tiene_permiso("reserva.crear"))
        self.assertTrue(cliente.tiene_permiso("reserva.consultar_historial_propio"))
        self.assertTrue(cliente.tiene_permiso("paquete.consultar_avance"))
        self.assertFalse(cliente.tiene_permiso("destino.crear"))

        self.assertEqual(administrador.nombre_rol, "Administrador")
        self.assertTrue(administrador.tiene_permiso("destino.modificar"))
        self.assertTrue(administrador.tiene_permiso("paquete.crear"))
        self.assertFalse(administrador.tiene_permiso("reserva.crear"))
        rol_guardado = self.repositorio.obtener(Rol, administrador.id_rol)
        self.assertEqual(
            administrador.obtener_permisos(),
            rol_guardado.obtener_permisos(),
        )

        nuevamente = RolDAO(self.repositorio).crear_predeterminados()
        self.assertEqual([rol.id_rol for rol in nuevamente], [rol.id_rol for rol in roles])
        self.assertEqual(len(self.repositorio.listar(Rol)), 2)

    def test_persistencia_entre_conexiones(self) -> None:
        with tempfile.TemporaryDirectory() as directorio:
            ruta = Path(directorio) / "journey.sqlite3"
            with RepositorioSQLite(ruta) as repositorio:
                creado = repositorio.crear(
                    Rol(nombre_rol="Administrador", descripcion="Gestión")
                )

            with RepositorioSQLite(ruta) as repositorio:
                self.assertEqual(
                    repositorio.obtener(Rol, creado.id_rol),
                    creado,
                )

    def test_crear_db_inicializa_el_esquema(self) -> None:
        conexion = crear_base_datos(":memory:")
        try:
            tablas = {
                fila["name"]
                for fila in conexion.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            self.assertIn("usuarios", tablas)
            self.assertIn("actividades_paquete", tablas)
            self.assertIn("pasajeros", tablas)
        finally:
            conexion.close()

    def test_transaccion_revierte_los_cambios_si_falla(self) -> None:
        with self.assertRaises(ValueError):
            with self.repositorio.transaccion():
                self.repositorio.crear(Rol(nombre_rol="Temporal"))
                raise ValueError("forzar rollback")

        self.assertEqual(self.repositorio.listar(Rol), [])

    def test_unicidad_y_restriccion_de_eliminacion_de_padres(self) -> None:
        rol = self.repositorio.crear(Rol(nombre_rol="Cliente"))
        self.repositorio.crear(
            Usuario(
                id_rol=rol.id_rol,
                nombre_completo="Ana",
                email="ana@example.com",
                password_hash="hash",
                documento_identidad="DOC-1",
            )
        )
        with self.assertRaises(sqlite3.IntegrityError):
            self.repositorio.crear(
                Usuario(
                    id_rol=rol.id_rol,
                    nombre_completo="Otra persona",
                    email="ana@example.com",
                    password_hash="hash",
                    documento_identidad="DOC-2",
                )
            )
        with self.assertRaises(sqlite3.IntegrityError):
            self.repositorio.eliminar(Rol, rol.id_rol)


if __name__ == "__main__":
    unittest.main()

import unittest
from contextlib import redirect_stdout
from datetime import date
from decimal import Decimal
from io import StringIO
from unittest.mock import patch

from src.dominio import PaqueteTuristico, Pasajero, Reserva, Rol, Usuario
from src.persistencia import RepositorioSQLite, RolDAO, UsuarioDAO
from src.presentacion.menu_cliente import MenuCliente
from src.presentacion.menu_principal import MenuPrincipal


class MenuConsolaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repositorio = RepositorioSQLite(":memory:")

    def tearDown(self) -> None:
        self.repositorio.cerrar()

    def test_menu_inicial_permite_entrar_a_cualquier_rol_sin_autenticacion(self) -> None:
        entrada = ["2", "0", "1", "0", "0"]
        salida = StringIO()
        with patch("builtins.input", side_effect=entrada), redirect_stdout(salida):
            MenuPrincipal(self.repositorio).ejecutar()

        texto = salida.getvalue()
        self.assertIn("Menú Cliente", texto)
        self.assertIn("Menú Administrador", texto)
        self.assertIn("no se solicita autenticación", texto)

    def test_menu_cliente_crea_reserva_pasajeros_y_descuenta_cupos(self) -> None:
        rol_cliente = next(
            rol
            for rol in RolDAO(self.repositorio).crear_predeterminados()
            if rol.nombre_rol == "Cliente"
        )
        cliente = UsuarioDAO(self.repositorio).crear(
            Usuario(
                id_rol=rol_cliente.id_rol,
                nombre_completo="Ana",
                email="ana@example.com",
                password_hash="hash",
                documento_identidad="DOC-1",
            )
        )
        paquete = self.repositorio.crear(
            PaqueteTuristico(
                nombre_paquete="Cordillera",
                fecha_inicio=date(2026, 12, 1),
                fecha_fin=date(2026, 12, 2),
                costo_total=Decimal("125"),
                cupos_totales=4,
                cupos_disponibles=4,
            )
        )
        menu = MenuCliente(self.repositorio)
        menu.usuario_actual = cliente
        entrada = [
            "6",
            str(paquete.id_paquete),
            "2",
            "Ana",
            "DOC-A",
            "1990-01-01",
            "555-111",
            "Luis",
            "DOC-B",
            "1988-02-02",
            "555-222",
            "",
            "0",
        ]
        salida = StringIO()
        with patch("builtins.input", side_effect=entrada), redirect_stdout(salida):
            menu.ejecutar()

        reserva = self.repositorio.listar_por(
            Reserva, id_usuario=cliente.id_usuario
        )[0]
        pasajeros = self.repositorio.listar_por(
            Pasajero, id_reserva=reserva.id_reserva
        )
        paquete_actualizado = self.repositorio.obtener(
            PaqueteTuristico, paquete.id_paquete
        )
        self.assertEqual(len(pasajeros), 2)
        self.assertTrue(pasajeros[0].es_titular)
        self.assertFalse(pasajeros[1].es_titular)
        self.assertEqual(reserva.monto_total, Decimal("250"))
        self.assertEqual(paquete_actualizado.cupos_disponibles, 2)
        self.assertIn("Reserva confirmada", salida.getvalue())


if __name__ == "__main__":
    unittest.main()

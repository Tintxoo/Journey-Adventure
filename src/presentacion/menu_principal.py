from src.persistencia import RepositorioSQLite
from .menu_administrador import MenuAdministrador
from .menu_cliente import MenuCliente
from .menu_base import limpiar_terminal, pausar


class MenuPrincipal:
    def __init__(self, repositorio: RepositorioSQLite) -> None:
        self.repositorio = repositorio

    def ejecutar(self) -> None:
        while True:
            limpiar_terminal()
            print("\n=== Journey Adventure ===")
            print("1. Menú Administrador")
            print("2. Menú Cliente")
            print("0. Salir")
            print("Acceso libre de demostración: no se solicita autenticación.")
            opcion = input("Selecciona un menú: ").strip()
            if opcion == "1":
                MenuAdministrador(self.repositorio).ejecutar()
            elif opcion == "2":
                MenuCliente(self.repositorio).ejecutar()
            elif opcion == "0":
                print("Hasta pronto.")
                return
            else:
                print("Opción no válida.")
                pausar()

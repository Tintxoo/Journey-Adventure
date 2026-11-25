from src.persistencia import RepositorioSQLite, RolDAO
from src.presentacion.menu_principal import MenuPrincipal


def main() -> None:
    with RepositorioSQLite() as repositorio:
        RolDAO(repositorio).crear_predeterminados()
        MenuPrincipal(repositorio).ejecutar()


if __name__ == "__main__":
    main()

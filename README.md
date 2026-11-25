# Journey-Adventure

## Dominio y persistencia

Las entidades del diagrama UML están en `src/dominio` y sus operaciones CRUD
se realizan mediante `RepositorioSQLite`, en `src/persistencia`. La base de
datos y su esquema están definidos en `src/persistencia/crear_db.py`; también
se puede crear por separado con `python -m src.persistencia.crear_db`. El
repositorio inicializa el esquema automáticamente y guarda por defecto en
`data/journey_adventure.sqlite3`. Se puede proporcionar otra ruta o usar
`":memory:"` para una base temporal.

```python
from src.dominio import Rol
from src.persistencia import RepositorioSQLite

with RepositorioSQLite() as repositorio:
    rol = repositorio.crear(Rol(nombre_rol="Cliente", descripcion="Cliente"))
    encontrado = repositorio.obtener(Rol, rol.id_rol)
    encontrado.descripcion = "Cliente registrado"
    repositorio.actualizar(encontrado)
    repositorio.eliminar(Rol, rol.id_rol)
```

`eliminar` desactiva destinos (eliminación lógica) y elimina las demás entidades
físicamente. Las claves foráneas impiden eliminar entidades que aún tienen
registros relacionados.

Los DAO tipados están directamente en `src/persistencia` y reutilizan el CRUD de
`RepositorioSQLite`: `RolDAO`, `UsuarioDAO`, `DestinoDAO`,
`PaqueteTuristicoDAO`, `PaqueteDestinoDAO`, `ActividadPaqueteDAO`,
`ReservaDAO` y `PasajeroDAO`. Por ejemplo:

```python
from src.persistencia import RepositorioSQLite
from src.persistencia import RolDAO

with RepositorioSQLite() as repositorio:
    rol_dao = RolDAO(repositorio)
    rol = rol_dao.crear_predeterminados()[0]
    permisos = rol.obtener_permisos()
```

Para insertar los roles iniciales una sola vez, llama
`RolDAO(repositorio).crear_predeterminados()`. El cliente puede registrarse,
autenticarse, consultar destinos y paquetes disponibles, crear reservas y
consultar sus propias reservas y pasajeros. El administrador puede
autenticarse, gestionar destinos y crear paquetes. Los permisos se consultan
con `rol.obtener_permisos()` o `rol.tiene_permiso("destino.crear")`.

Las actividades se asocian a un paquete usando `dia_relativo` (el día 1 es la
fecha de inicio). `repositorio.obtener_avance_paquete(id_paquete)` devuelve el
porcentaje completado, las actividades por estado (`pendiente`, `en_curso`,
`realizada`), la etapa actual y la próxima actividad. El cálculo usa la fecha
actual; se puede pasar otra fecha para consultar el avance a una fecha concreta.
El permiso `paquete.consultar_avance` queda habilitado para el rol Cliente.

```python
from datetime import date, timedelta
from decimal import Decimal

from src.dominio import ActividadPaquete, PaqueteTuristico
from src.persistencia import RepositorioSQLite

with RepositorioSQLite() as repositorio:
    paquete = repositorio.crear(
        PaqueteTuristico(
            nombre_paquete="Aventura",
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=2),
            costo_total=Decimal("300"),
            cupos_totales=10,
            cupos_disponibles=10,
        )
    )
    repositorio.crear(
        ActividadPaquete(
            id_paquete=paquete.id_paquete,
            nombre="Excursión",
            dia_relativo=2,
        )
    )
    avance = repositorio.obtener_avance_paquete(paquete.id_paquete)
```

Pruebas: `python -m unittest discover -s tests`

## Menús de consola

Inicia la aplicación con `python -m src.main`. Al comenzar puedes entrar
directamente al menú Cliente o Administrador; por ahora no se solicita
autenticación ni se restringe el acceso entre roles. La terminal se limpia al
redibujar los menús y espera Enter después de cada operación para que puedas
leer el resultado.
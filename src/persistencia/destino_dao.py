from src.dominio import Destino
from .base_dao import BaseDAO


class DestinoDAO(BaseDAO[Destino]):
    entidad = Destino

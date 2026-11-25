from src.dominio import Usuario
from .base_dao import BaseDAO


class UsuarioDAO(BaseDAO[Usuario]):
    entidad = Usuario

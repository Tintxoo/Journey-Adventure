import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import ClassVar


@dataclass
class Usuario:
    id_usuario: int | None = None
    id_rol: int = 0
    nombre_completo: str = ""
    email: str = ""
    password_hash: str = ""
    documento_identidad: str = ""
    telefono: str = ""
    intentos_fallidos: int = 0
    activo: bool = True
    fecha_registro: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    tabla: ClassVar[str] = "usuarios"
    clave_primaria: ClassVar[str] = "id_usuario"

    def validar_datos(self) -> bool:
        return bool(
            self.nombre_completo.strip()
            and "@" in self.email
            and self.password_hash.strip()
            and self.documento_identidad.strip()
            and self.intentos_fallidos >= 0
        )

    @staticmethod
    def crear_password_hash(contrasena: str) -> str:
        if len(contrasena) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", contrasena.encode(), salt, 310_000)
        return f"pbkdf2_sha256$310000${salt.hex()}${digest.hex()}"
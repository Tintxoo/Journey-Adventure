import os
import sqlite3
from collections.abc import Callable
from dataclasses import fields
from datetime import date
from decimal import Decimal
import sys


def pedir_texto(mensaje: str, valor_actual: str | None = None) -> str:
    while True:
        sufijo = f" [{valor_actual}]" if valor_actual is not None else ""
        valor = input(f"{mensaje}{sufijo}: ").strip()
        if valor:
            return valor
        if valor_actual is not None:
            return valor_actual
        print("El valor es obligatorio.")


def pedir_entero(
    mensaje: str,
    valor_actual: int | None = None,
    minimo: int | None = None,
) -> int:
    while True:
        sufijo = f" [{valor_actual}]" if valor_actual is not None else ""
        valor = input(f"{mensaje}{sufijo}: ").strip()
        try:
            resultado = valor_actual if not valor and valor_actual is not None else int(valor)
        except ValueError:
            print("Ingresa un número entero válido.")
            continue
        if resultado is None or (minimo is not None and resultado < minimo):
            print(f"El valor debe ser mayor o igual a {minimo}.")
            continue
        return resultado


def pedir_decimal(mensaje: str, valor_actual: Decimal | None = None) -> Decimal:
    while True:
        sufijo = f" [{valor_actual}]" if valor_actual is not None else ""
        valor = input(f"{mensaje}{sufijo}: ").strip()
        try:
            return valor_actual if not valor and valor_actual is not None else Decimal(valor)
        except (ValueError, ArithmeticError):
            print("Ingresa un valor decimal válido.")


def pedir_fecha(mensaje: str, valor_actual: date | None = None) -> date:
    while True:
        sufijo = f" [{valor_actual.isoformat()}]" if valor_actual is not None else ""
        valor = input(f"{mensaje} (AAAA-MM-DD){sufijo}: ").strip()
        if not valor and valor_actual is not None:
            return valor_actual
        try:
            return date.fromisoformat(valor)
        except ValueError:
            print("Ingresa una fecha válida con formato AAAA-MM-DD.")


def pedir_booleano(mensaje: str, valor_actual: bool) -> bool:
    predeterminado = "s" if valor_actual else "n"
    while True:
        valor = input(f"{mensaje} (s/n) [{predeterminado}]: ").strip().casefold()
        if not valor:
            return valor_actual
        if valor in ("s", "si", "sí"):
            return True
        if valor in ("n", "no"):
            return False
        print("Responde s o n.")


def mostrar_entidades(entidades: list[object]) -> None:
    if not entidades:
        print("No hay registros.")
        return
    for entidad in entidades:
        datos = ", ".join(
            f"{campo.name}={getattr(entidad, campo.name)}"
            for campo in fields(entidad)
        )
        print(datos)


def ejecutar_accion(accion: Callable[[], None]) -> None:
    try:
        accion()
    except (ValueError, LookupError, sqlite3.IntegrityError) as error:
        print(f"No se pudo completar la operación: {error}")


def limpiar_terminal() -> None:
    if sys.stdout.isatty():
        os.system("cls" if os.name == "nt" else "clear")


def pausar() -> None:
    input("\nPresiona Enter para continuar...")

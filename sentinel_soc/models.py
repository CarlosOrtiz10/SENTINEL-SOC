"""Entidades del dominio: valores sintéticos, sin datos operativos reales."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    CRITICAL = "CRITICA"
    HIGH = "ALTA"
    MEDIUM = "MEDIA"
    LOW = "BAJA"


@dataclass(frozen=True, slots=True)
class Incident:
    id: int
    asset: str
    category: str
    severity: Severity

    def __post_init__(self) -> None:
        if type(self.id) is not int:
            raise TypeError("El identificador debe ser un entero")
        if not isinstance(self.asset, str) or not isinstance(self.category, str):
            raise TypeError("Activo y categoría deben ser texto")
        if self.id < 1:
            raise ValueError("El identificador debe ser positivo")
        if not self.asset.strip() or not self.category.strip():
            raise ValueError("Activo y categoría son obligatorios")
        if not isinstance(self.severity, Severity):
            raise TypeError("Se requiere un valor válido de Severity")

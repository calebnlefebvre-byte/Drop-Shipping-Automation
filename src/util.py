from typing import Optional


def float_or_none(value: Optional[str]) -> Optional[float]:
    return float(value) if value else None


def int_or_none(value: Optional[str]) -> Optional[int]:
    return int(value) if value else None

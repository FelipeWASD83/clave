"""Chaves e tokens guardados em dados/segredos.json.

No Windows o valor é criptografado com o DPAPI (CryptProtectData), que amarra o
segredo ao usuário do Windows: o arquivo copiado para outro PC ou outra conta
não abre. Fora do Windows o valor fica só em base64, com permissão 600.
"""
from __future__ import annotations

import base64
import json
import os
import sys
import threading

from config import DADOS

_trava = threading.Lock()
_ENTROPIA = b"clave-segredos-v1"


if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    class _Blob(ctypes.Structure):
        _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    _crypt32 = ctypes.windll.crypt32
    _kernel32 = ctypes.windll.kernel32

    def _blob(dados: bytes) -> _Blob:
        buf = ctypes.create_string_buffer(dados, len(dados))
        return _Blob(len(dados), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))

    def _proteger(dados: bytes) -> bytes:
        entrada, entropia, saida = _blob(dados), _blob(_ENTROPIA), _Blob()
        if not _crypt32.CryptProtectData(ctypes.byref(entrada), "clave", ctypes.byref(entropia),
                                         None, None, 0x1, ctypes.byref(saida)):
            raise OSError("CryptProtectData falhou")
        try:
            return ctypes.string_at(saida.pbData, saida.cbData)
        finally:
            _kernel32.LocalFree(saida.pbData)

    def _abrir(dados: bytes) -> bytes:
        entrada, entropia, saida = _blob(dados), _blob(_ENTROPIA), _Blob()
        if not _crypt32.CryptUnprotectData(ctypes.byref(entrada), None, ctypes.byref(entropia),
                                           None, None, 0x1, ctypes.byref(saida)):
            raise OSError("CryptUnprotectData falhou")
        try:
            return ctypes.string_at(saida.pbData, saida.cbData)
        finally:
            _kernel32.LocalFree(saida.pbData)
else:
    def _proteger(dados: bytes) -> bytes:
        return dados

    def _abrir(dados: bytes) -> bytes:
        return dados


def _arquivo():
    return DADOS / "segredos.json"


def _ler_tudo() -> dict:
    try:
        return json.loads(_arquivo().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _gravar_tudo(dados: dict) -> None:
    DADOS.mkdir(parents=True, exist_ok=True)
    tmp = _arquivo().with_suffix(".tmp")
    tmp.write_text(json.dumps(dados, indent=2), encoding="utf-8")
    os.replace(tmp, _arquivo())
    if sys.platform != "win32":
        os.chmod(_arquivo(), 0o600)


def guardar(nome: str, valor: str) -> None:
    with _trava:
        tudo = _ler_tudo()
        tudo[nome] = base64.b64encode(_proteger(valor.encode("utf-8"))).decode("ascii")
        _gravar_tudo(tudo)


def ler(nome: str) -> str | None:
    with _trava:
        bruto = _ler_tudo().get(nome)
    if not bruto:
        return None
    try:
        return _abrir(base64.b64decode(bruto)).decode("utf-8")
    except (OSError, ValueError):
        return None


def apagar(nome: str) -> None:
    with _trava:
        tudo = _ler_tudo()
        if tudo.pop(nome, None) is not None:
            _gravar_tudo(tudo)


def existe(nome: str) -> bool:
    return ler(nome) is not None


def mascarar(valor: str | None) -> str:
    if not valor:
        return ""
    return valor[:10] + "…" + valor[-4:] if len(valor) > 18 else "…"

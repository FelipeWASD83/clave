"""Preparação comum dos testes: pasta de dados temporária ANTES de carregar os módulos do servidor."""
import os
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if "CLAVE_DADOS" not in os.environ or "clave-testes-" not in os.environ["CLAVE_DADOS"]:
    os.environ["CLAVE_DADOS"] = tempfile.mkdtemp(prefix="clave-testes-")
os.environ.pop("CLAVE_API_FALSA", None)
sys.path.insert(0, str(RAIZ / "servidor"))
DADOS = Path(os.environ["CLAVE_DADOS"])

"""Roda uma rotina pelo Agendador de Tarefas do Windows: rodar_rotina.py <id> [--dados <pasta>].

Se o Clave estiver aberto, só pede para o app rodar (assim não há dois processos mexendo no mesmo banco
e a conversa aparece na hora). Com o app fechado, roda aqui mesmo, sem janela, e avisa pela notificação
do Windows quando terminar.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def _pre():
    argv = sys.argv[1:]
    if "--dados" in argv and argv.index("--dados") + 1 < len(argv):
        os.environ["CLAVE_DADOS"] = argv[argv.index("--dados") + 1]


_pre()

import config  # noqa: E402


def _app_aberto() -> int | None:
    try:
        info = json.loads((config.DADOS / "servidor.json").read_text(encoding="utf-8"))
        import iniciar
        if iniciar.processo_vivo(int(info["pid"])):
            return int(info["porta"])
    except (OSError, ValueError, KeyError):
        pass
    return None


def _pedir_ao_app(porta: int, rid: str) -> bool:
    try:
        segredo = (config.DADOS / "sessao.key").read_text(encoding="ascii").strip()
        req = urllib.request.Request(f"http://127.0.0.1:{porta}/api/rotinas/{rid}/rodar", data=b"{}", method="POST",
                                     headers={"Content-Type": "application/json", "Host": f"127.0.0.1:{porta}",
                                              "Origin": f"http://127.0.0.1:{porta}",
                                              "Cookie": f"clave_sessao={segredo}"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status == 200
    except Exception:
        return False


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--dados" in sys.argv:
        args = [a for a in args if a != os.environ.get("CLAVE_DADOS")]
    if not args:
        print("uso: rodar_rotina.py <id da rotina>", file=sys.stderr)
        return 2
    rid = args[0]
    porta = _app_aberto()
    if porta and _pedir_ao_app(porta, rid):
        return 0
    import banco
    import rotinas
    r = banco.rotina(rid)
    if not r or not r.get("ligada"):
        return 0
    try:
        info = rotinas.rodar(rid, "agendador")
    except rotinas.ErroRotina as e:
        rotinas.notificar_windows(f"Clave: {r['nome']}", f"A rotina não rodou: {e}")
        return 1
    import execucao
    ex = execucao.pegar(info["execucao"])
    ex.thread.join()
    final = banco.rotina(rid) or {}
    rotinas.notificar_windows(f"Clave: {r['nome']}", f"Rotina {final.get('ultimo_status') or 'terminada'}. "
                              "Abra o Clave para ver o resultado.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

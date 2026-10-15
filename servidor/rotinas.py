"""Rotinas: um pedido salvo que roda sozinho (todo dia, em alguns dias da semana ou a cada N horas).

Roda de dois jeitos: com o Clave aberto (o servidor confere a cada 30 s se alguma venceu) ou, se a pessoa
pedir, pelo Agendador de Tarefas do Windows, que roda o rodar_rotina.py mesmo com o app fechado (se o
app estiver aberto, ele só avisa o app, que roda no lugar dele).

Numa rotina ninguém está olhando: ela só faz o que as regras de permissão já liberam (ler na pasta,
mais o que tiver regra de permitir). Se precisar de um OK, ela para e conta o que precisaria. Cada
rodada tem teto de gasto próprio.
"""
from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

import banco
import config
import orcamento
from i18n import t

DIAS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
NOMES_DIAS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]  # mostrar com t()
TAREFA_WINDOWS = "Clave\\Rotina {id}"
_rodando: dict[str, str] = {}  # rotina -> execução
_trava = threading.Lock()
_avisos: list[dict] = []       # o que a interface mostra como notificação


class ErroRotina(Exception):
    pass


def _hora(texto: str) -> tuple[int, int]:
    try:
        h, m = str(texto or "08:00").split(":")
        h, m = int(h), int(m)
        if 0 <= h < 24 and 0 <= m < 60:
            return h, m
    except ValueError:
        pass
    raise ErroRotina(t("Hora inválida; use HH:MM, por exemplo 08:30."))


def proxima(quando: dict, depois: float | None = None) -> float:
    """Próximo horário (timestamp) depois de `depois`."""
    base = datetime.fromtimestamp(depois if depois is not None else time.time())
    tipo = (quando or {}).get("tipo") or "diaria"
    if tipo == "horas":
        n = max(1, min(24, int(quando.get("a_cada") or 1)))
        alvo = base.replace(second=0, microsecond=0) + timedelta(hours=n)
        return alvo.timestamp()
    h, m = _hora(quando.get("hora"))
    dias = sorted({int(d) for d in (quando.get("dias") or []) if str(d).isdigit() and 0 <= int(d) <= 6})
    if tipo == "semanal" and not dias:
        raise ErroRotina(t("Escolha pelo menos um dia da semana."))
    for k in range(0, 8):
        dia = (base + timedelta(days=k)).replace(hour=h, minute=m, second=0, microsecond=0)
        if dia <= base:
            continue
        if tipo == "semanal" and dia.weekday() not in dias:
            continue
        return dia.timestamp()
    raise ErroRotina(t("Não deu para calcular o próximo horário."))


def descrever(quando: dict) -> str:
    tipo = (quando or {}).get("tipo") or "diaria"
    if tipo == "horas":
        n = int(quando.get("a_cada") or 1)
        return t("a cada hora") if n == 1 else t("a cada {n} horas", n=n)
    hora = quando.get("hora") or "08:00"
    if tipo == "semanal":
        dias = ", ".join(t(NOMES_DIAS[int(d)]) for d in sorted(quando.get("dias") or []))
        return t("{dias}, às {hora}", dias=dias, hora=hora)
    return t("todo dia às {hora}", hora=hora)


def validar(nome: str, dados: dict) -> dict:
    if not str(nome or "").strip():
        raise ErroRotina(t("Dê um nome à rotina."))
    prompt = str(dados.get("prompt") or "").strip()
    if not prompt:
        raise ErroRotina(t("Escreva o que a rotina deve fazer."))
    modo = "code" if dados.get("modo") == "code" else "chat"
    pasta = None
    if modo == "code":
        pasta = str(dados.get("pasta") or "")
        if not pasta or not Path(pasta).is_dir():
            raise ErroRotina(t("Escolha uma pasta que exista para a rotina trabalhar."))
        pasta = str(Path(pasta).resolve())
    quando = dict(dados.get("quando") or {"tipo": "diaria", "hora": "08:00"})
    if quando.get("tipo") not in ("diaria", "semanal", "horas"):
        raise ErroRotina(t("Frequência inválida."))
    proxima(quando)  # confere
    try:
        teto = float(dados["teto_usd"]) if dados.get("teto_usd") not in (None, "") else 0.5
    except (TypeError, ValueError):
        raise ErroRotina(t("Teto de gasto inválido."))
    if teto <= 0 or teto > 50:
        raise ErroRotina(t("O teto por rodada fica entre US$ 0,01 e US$ 50."))
    return {"prompt": prompt, "modo": modo, "pasta": pasta, "quando": quando, "teto_usd": round(teto, 2),
            "modelo": str(dados.get("modelo") or "claude-sonnet-5-5"), "esforco": str(dados.get("esforco") or "medium"),
            "busca_web": bool(dados.get("busca_web")), "agendador": bool(dados.get("agendador"))}


def salvar(rid: str | None, nome: str, dados: dict, ligada: bool = True) -> dict:
    limpos = validar(nome, dados)
    antiga = banco.rotina(rid) if rid else None
    r = banco.salvar_rotina(rid, str(nome).strip()[:80], limpos, ligada, proxima(limpos["quando"]))
    if sys.platform == "win32":
        if antiga and antiga.get("agendador") and (not limpos["agendador"] or not ligada):
            desagendar_windows(r["id"])
        if limpos["agendador"] and ligada:
            agendar_windows(r)
    return banco.rotina(r["id"])


def apagar(rid: str) -> None:
    r = banco.rotina(rid)
    if r and r.get("agendador") and sys.platform == "win32":
        desagendar_windows(rid)
    banco.apagar_rotina(rid)


def desligar_todas() -> int:
    """"Sair da conta": sem chave nenhuma rotina conseguiria rodar; elas ficam salvas, desligadas e fora do
    Agendador do Windows até a pessoa religar."""
    n = 0
    for r in banco.listar_rotinas():
        if r.get("agendador") and sys.platform == "win32":
            desagendar_windows(r["id"])
        if r.get("ligada"):
            banco.marcar_rotina(r["id"], ligada=0)
            n += 1
    return n


def desagendar_todas() -> None:
    """Desinstalar: nenhuma tarefa "Clave\\Rotina ..." pode sobrar no Agendador apontando para uma pasta apagada."""
    if sys.platform != "win32":
        return
    for r in banco.listar_rotinas():
        desagendar_windows(r["id"])


def avisos_desde(n: int) -> tuple[list[dict], int]:
    with _trava:
        return _avisos[n:], len(_avisos)


def _avisar(aviso: dict) -> None:
    with _trava:
        _avisos.append({**aviso, "em": time.time()})


def rodando(rid: str) -> bool:
    import execucao
    eid = _rodando.get(rid)
    ex = execucao.pegar(eid) if eid else None
    return bool(ex and ex.status in ("rodando", "esperando"))


def rodar(rid: str, motivo: str = "agendada") -> dict:
    """Começa uma rodada agora. Devolve {conversa, execucao}."""
    import execucao
    import fluxos
    import sistema
    r = banco.rotina(rid)
    if not r:
        raise ErroRotina(t("Rotina não encontrada."))
    if rodando(rid):
        raise ErroRotina(t("Esta rotina já está rodando."))
    ok, motivo_teto = orcamento.pode_gastar()
    if not ok:
        banco.marcar_rotina(rid, ultima=time.time(), ultimo_status=t("não rodou: {motivo}", motivo=motivo_teto))
        _avisar({"tipo": "rotina", "rotina": rid, "nome": r["nome"], "status": t("bloqueada"), "texto": motivo_teto})
        raise ErroRotina(motivo_teto)
    cfg = config.carregar()
    agora = datetime.now()
    quando = t("{dia}/{mes} {hora}", dia=f"{agora.day:02d}", mes=f"{agora.month:02d}", hora=agora.strftime("%H:%M"))
    conv = banco.criar_conversa(modo=r["modo"], pasta=r.get("pasta"), titulo=t("Rotina: {nome} · {quando}", nome=r["nome"],
                                                                             quando=quando),
                                ajustes={"rotina": rid, "modelo": r["modelo"], "esforco": r["esforco"]})
    texto_sis = sistema.code(cfg, r["pasta"]) if r["modo"] == "code" else sistema.chat(cfg)
    texto_sis += "\n\n" + " ".join([
        t("Esta conversa é uma rotina automática: ninguém está acompanhando agora."),
        t("Faça o pedido do começo ao fim sem perguntar nada; se faltar informação, faça a suposição mais razoável e diga qual foi."),
        t("Ações que precisariam do OK de quem usa não rodam (a rotina para)."),
        t("Termine com um resumo curto do resultado."),
    ])
    banco.atualizar_conversa(conv["id"], sistema=texto_sis)
    banco.adicionar_mensagem(conv["id"], None, "user", [{"type": "text", "text": r["prompt"]}],
                             meta={"rotina": rid})
    op = {"modelo": r["modelo"], "esforco": r["esforco"], "pensar": True, "mostrar_raciocinio": True,
          "busca_web": r.get("busca_web"), "github": False, "rapido": False, "permissao": "perguntar", "rotina": True}
    ex = execucao.iniciar_sem_thread(conv["id"], op)
    ex.cofre = fluxos.Cofre(r["teto_usd"], "A rotina")  # o rótulo é chave de t(): traduzido ao mostrar
    _rodando[rid] = ex.id
    banco.marcar_rotina(rid, ultima=time.time(), ultimo_status=t("rodando"), ultima_conversa=conv["id"],
                        proxima=proxima(r["quando"]))

    def tocar():
        try:
            ex.rodar()
        finally:
            if ex.pediu_ok:
                st = t("parou: precisaria de OK para {acao}", acao=ex.pediu_ok.get("sugestao") or ex.pediu_ok.get("ferramenta"))
            elif ex.cofre.estourou():
                st = t("parou no teto de gasto")
            else:
                nomes = {"concluida": "concluída", "erro": "erro", "parada": "parada"}
                st = t(nomes[ex.status]) if ex.status in nomes else ex.status
            banco.marcar_rotina(rid, ultimo_status=st)
            _avisar({"tipo": "rotina", "rotina": rid, "nome": r["nome"], "status": st, "conversa": conv["id"],
                     "custo": round(ex.custo_total, 4)})
            _rodando.pop(rid, None)

    th = threading.Thread(target=tocar, name=f"rotina-{rid}", daemon=True)
    th.start()
    ex.thread = th
    return {"conversa": conv["id"], "execucao": ex.id, "motivo": motivo}


class Relogio(threading.Thread):
    """Com o app aberto, roda as rotinas que venceram (menos as do Agendador do Windows: ele cuida delas)."""

    def __init__(self):
        super().__init__(name="relogio-rotinas", daemon=True)
        self.parar = threading.Event()

    def run(self):
        while not self.parar.wait(30):
            try:
                self.uma_volta()
            except Exception:
                import traceback
                traceback.print_exc()

    def uma_volta(self, agora: float | None = None) -> list[str]:
        agora = agora or time.time()
        rodadas = []
        for r in banco.listar_rotinas():
            if not r["ligada"] or r.get("agendador") or not r.get("proxima") or r["proxima"] > agora:
                continue
            if rodando(r["id"]):
                continue
            atrasada = agora - r["proxima"] > 6 * 3600
            banco.marcar_rotina(r["id"], proxima=proxima(r["quando"], agora))
            if atrasada:  # o PC estava desligado: não roda uma pilha de atrasadas, só marca a próxima
                banco.marcar_rotina(r["id"], ultimo_status=t("pulada (o Clave estava fechado no horário)"))
                continue
            try:
                rodar(r["id"])
                rodadas.append(r["id"])
            except ErroRotina:
                pass
        return rodadas


# ---------------- Agendador de Tarefas do Windows ----------------

def _comando_windows(rid: str) -> str:
    pyw = Path(sys.executable).with_name("pythonw.exe")
    py = pyw if pyw.is_file() else Path(sys.executable)
    script = Path(__file__).resolve().parent / "rodar_rotina.py"
    dados = os.environ.get("CLAVE_DADOS")
    extra = f' --dados "{dados}"' if dados else ""
    return f'"{py}" "{script}" {rid}{extra}'


def agendar_windows(r: dict) -> None:
    q = r["quando"]
    args = ["schtasks", "/Create", "/F", "/TN", TAREFA_WINDOWS.format(id=r["id"]), "/TR", _comando_windows(r["id"])]
    if q["tipo"] == "horas":
        inicio = datetime.fromtimestamp(time.time() + 120).strftime("%H:%M")
        args += ["/SC", "HOURLY", "/MO", str(max(1, min(23, int(q.get("a_cada") or 1)))), "/ST", inicio]
    elif q["tipo"] == "semanal":
        args += ["/SC", "WEEKLY", "/D", ",".join(DIAS[int(d)] for d in sorted(q.get("dias") or [])),
                 "/ST", q.get("hora") or "08:00"]
    else:
        args += ["/SC", "DAILY", "/ST", q.get("hora") or "08:00"]
    p = subprocess.run(args, capture_output=True, text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if p.returncode != 0:
        raise ErroRotina(t("O Agendador de Tarefas do Windows recusou: {erro}", erro=(p.stderr or p.stdout).strip()))


def desagendar_windows(rid: str) -> None:
    subprocess.run(["schtasks", "/Delete", "/F", "/TN", TAREFA_WINDOWS.format(id=rid)], capture_output=True,
                   text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def agendada_no_windows(rid: str) -> bool:
    if sys.platform != "win32":
        return False
    p = subprocess.run(["schtasks", "/Query", "/TN", TAREFA_WINDOWS.format(id=rid)], capture_output=True, text=True,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    return p.returncode == 0


def notificar_windows(titulo: str, texto: str) -> None:
    """Notificação do Windows sem o app aberto (pela API de notificações, via PowerShell)."""
    if sys.platform != "win32":
        return

    def esc(s):
        return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("'", "&apos;")
                .replace('"', "&quot;"))
    xml = (f"<toast><visual><binding template='ToastGeneric'><text>{esc(titulo)}</text><text>{esc(texto)}</text>"
           "</binding></visual></toast>")
    script = (
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null;"
        "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null;"
        "$x = New-Object Windows.Data.Xml.Dom.XmlDocument; $x.LoadXml($env:CLAVE_TOAST);"
        "$t = [Windows.UI.Notifications.ToastNotification]::new($x);"
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("
        "'{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe').Show($t)")
    try:
        subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                       env={**os.environ, "CLAVE_TOAST": xml}, capture_output=True, timeout=20,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.TimeoutExpired):
        pass

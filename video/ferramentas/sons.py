"""Efeitos sonoros do vídeo, sintetizados aqui (sem amostra de ninguém): toque, tique, impressora, folha e selo.
Ficam baixos, por baixo da narração. Saída: public/sons/*.wav (48 kHz, 16 bits, estéreo)."""
import wave
from pathlib import Path

import numpy as np

TAXA = 48000
PASTA = Path(__file__).resolve().parent.parent / "public" / "sons"
rng = np.random.default_rng(11)


def tempo(segundos):
    return np.arange(int(TAXA * segundos)) / TAXA


def passa_baixa(sinal, corte_hz):
    corte = np.broadcast_to(np.asarray(corte_hz, dtype=float), sinal.shape)
    a = 1 - np.exp(-2 * np.pi * corte / TAXA)
    saida = np.empty_like(sinal)
    y = 0.0
    for i, (x, k) in enumerate(zip(sinal, a)):
        y += k * (x - y)
        saida[i] = y
    return saida


def passa_alta(sinal, corte_hz):
    return sinal - passa_baixa(sinal, corte_hz)


def gravar(nome, sinal, pico_db=-6):
    if sinal.ndim == 1:
        sinal = np.stack([sinal, sinal], axis=1)
    fade = min(256, len(sinal) // 4)
    sinal[-fade:] *= np.linspace(1, 0, fade)[:, None]
    sinal = sinal / (np.max(np.abs(sinal)) or 1) * 10 ** (pico_db / 20)
    PASTA.mkdir(parents=True, exist_ok=True)
    with wave.open(str(PASTA / nome), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(TAXA)
        w.writeframes((sinal * 32767).astype("<i2").tobytes())
    print("ok", nome, f"{len(sinal) / TAXA:.2f} s")


def toque():
    """Clique de interface (botão, cartão chegando)."""
    t = tempo(0.12)
    tom = np.sin(2 * np.pi * 1180 * t) * np.exp(-t * 55) + 0.4 * np.sin(2 * np.pi * 2360 * t) * np.exp(-t * 80)
    ataque = passa_alta(rng.standard_normal(len(t)), 3500) * np.exp(-t * 500) * 0.5
    return tom + ataque


def tique():
    """O tique seco do relógio do limite."""
    t = tempo(0.05)
    return passa_alta(rng.standard_normal(len(t)), 2000) * np.exp(-t * 260)


def impressora():
    """A fita de recibo imprimindo uma linha: um zumbido curto em pulsos."""
    t = tempo(0.34)
    pulsos = (np.sin(2 * np.pi * 42 * t) > 0.2).astype(float)
    motor = np.sin(2 * np.pi * 180 * t) * 0.5 + passa_baixa(rng.standard_normal(len(t)), 2600) * 0.9
    env = np.minimum(1, t * 60) * np.minimum(1, (t[-1] - t) * 40)
    return passa_alta(motor * pulsos * env, 150)


def folha():
    """A folha passando na troca de cena: ruído macio que abre e fecha."""
    t = tempo(0.5)
    x = t / t[-1]
    s = passa_alta(passa_baixa(rng.standard_normal(len(t)), 600 + 3800 * np.sin(np.pi * x) ** 2), 200)
    s *= np.sin(np.pi * x) ** 1.8
    return np.stack([s * (0.3 + 0.7 * x), s * (1 - 0.7 * x)], axis=1)


def selo():
    """Batida grave e curta quando a marca chega."""
    t = tempo(0.7)
    freq = 70 + 60 * np.exp(-t * 18)
    grave = np.sin(2 * np.pi * np.cumsum(freq) / TAXA) * np.exp(-t * 6)
    corpo = passa_baixa(rng.standard_normal(len(t)), 700) * np.exp(-t * 30) * 0.6
    return grave + corpo


def trilha(segundos=100):
    """Uma cama bem calma por baixo da narração: quatro acordes abertos (Rém7M, Sim7, Sol7M, Lá6) que se
    cruzam devagar, de senos levemente desafinados entre si (o "coro"), com o grave da tônica. Sem bateria."""
    t = tempo(segundos)
    acordes = [
        [146.83, 185.00, 220.00, 277.18],  # Rém7M
        [123.47, 146.83, 185.00, 220.00],  # Sim7
        [98.00, 123.47, 146.83, 185.00],  # Sol7M
        [110.00, 138.59, 164.81, 185.00],  # Lá6
    ]
    dura = 6.0
    saida_e = np.zeros(len(t))
    saida_d = np.zeros(len(t))
    for k in range(int(segundos / dura) + 1):
        notas = acordes[k % 4]
        inicio = k * dura - 1.5
        x = t - inicio
        env = np.clip(x / 2.2, 0, 1) * np.clip((dura + 1.5 - x) / 2.2, 0, 1)
        env = np.sin(env * np.pi / 2) ** 2
        if not env.any():
            continue
        for j, hz in enumerate(notas):
            for desvio, lado in ((-0.0018, 0), (0.0021, 1)):
                fase = 2 * np.pi * hz * (1 + desvio) * t + j * 1.3
                onda = np.sin(fase) + 0.18 * np.sin(2 * fase) + 0.05 * np.sin(3 * fase)
                (saida_e if lado == 0 else saida_d)[:] += onda * env * (0.9 - j * 0.12)
        grave = np.sin(2 * np.pi * notas[0] / 2 * t) * env * 0.7
        saida_e += grave
        saida_d += grave
    respira = 0.85 + 0.15 * np.sin(2 * np.pi * t / 9)
    return np.stack([saida_e * respira, saida_d * respira], axis=1)


if __name__ == "__main__":
    gravar("trilha.wav", trilha(), -14)
    gravar("toque.wav", toque())
    gravar("tique.wav", tique(), -10)
    gravar("impressora.wav", impressora(), -9)
    gravar("folha.wav", folha(), -8)
    gravar("selo.wav", selo(), -5)

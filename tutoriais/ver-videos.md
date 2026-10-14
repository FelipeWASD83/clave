---
titulo: Fazer o Claude ver vídeos
trilha: 4. Ir além
ordem: 32
duracao: 5 min
resumo: A skill ver-video baixa o vídeo, tira quadros e transcreve a fala para o Claude analisar.
---

O Claude não assiste vídeo diretamente. A skill **ver-video** contorna isso: ela transforma o vídeo em coisas que ele lê, **imagens** (quadros tirados de tempo em tempo, montados em folhas com o horário escrito) e **texto** (a fala transcrita, com o tempo de cada trecho).

Funciona com arquivos do computador (mp4, mov, mkv...) e com links do YouTube, TikTok, Instagram, X, Reddit e centenas de outros sites.

## O que precisa instalar (uma vez)

A skill usa três programas gratuitos:

- **ffmpeg**: abre e corta vídeos;
- **yt-dlp**: baixa vídeos de sites;
- **faster-whisper**: transcreve a fala, no seu computador (o áudio não vai para a internet).

Na primeira vez, o Claude percebe que falta e roda o instalador que vem com a skill (ele pede o seu OK). Com placa de vídeo NVIDIA a transcrição é bem mais rápida; sem ela também funciona, só demora mais.

## Como usar

No modo Code (a skill vem no Clave e no [modelo de pasta](#/aprender/modelo-de-pasta)), mande o link ou o caminho do arquivo:

```experimentar-code
Veja este vídeo e me diga do que ele trata, em 5 tópicos: https://www.youtube.com/watch?v=jNQXAC9IVRw
```

Outros pedidos:

- "Transcreva a fala deste vídeo com os tempos."
- "Neste tutorial, em que minuto ele mostra como configurar a impressora?"
- "Olhe só do minuto 2:00 ao 3:30 e descreva o que acontece."

## Limites

- Ele vê **quadros soltos**, não o movimento contínuo: vídeo longo vira quase uma sequência de fotos.
- Ele **não ouve música** nem sons, só a fala transcrita.
- Vídeo privado ou com login pode precisar dos cookies do seu navegador (o Claude explica quando for o caso).
- Baixe só vídeos que você tem direito de usar.

---
titulo: Make Claude watch videos
trilha: 4. Going further
ordem: 32
duracao: 5 min
resumo: The ver-video skill downloads the video, takes frames and transcribes the speech for Claude to analyze.
---

Claude can't watch video directly. The **ver-video** skill works around that: it turns the video into things Claude can read, **images** (frames taken every so often, put together into sheets with the time written on them) and **text** (the speech transcribed, with the time of each part).

It works with files on your computer (mp4, mov, mkv...) and with links from YouTube, TikTok, Instagram, X, Reddit and hundreds of other sites.

## What you need to install (once)

The skill uses three free programs:

- **ffmpeg**: opens and cuts videos;
- **yt-dlp**: downloads videos from websites;
- **faster-whisper**: transcribes speech, on your computer (the audio doesn't go to the internet).

The first time, Claude notices something is missing and runs the installer that comes with the skill (it asks for your OK). With an NVIDIA graphics card, transcription is a lot faster; without one it still works, it just takes longer.

## How to use it

In Code mode (the skill comes with Clave and with the [folder template](#/aprender/modelo-de-pasta)), send the link or the file path:

```experimentar-code
Watch this video and tell me what it is about, in 5 bullet points: https://www.youtube.com/watch?v=jNQXAC9IVRw
```

Other requests:

- "Transcribe the speech in this video with timestamps."
- "In this tutorial, at what minute does he show how to set up the printer?"
- "Look only from minute 2:00 to 3:30 and describe what happens."

## Limits

- It sees **separate frames**, not continuous motion: a long video becomes almost a sequence of photos.
- It **doesn't hear music** or sounds, only the transcribed speech.
- A private video, or one that needs a login, may need your browser's cookies (Claude explains when that is the case).
- Only download videos you have the right to use.

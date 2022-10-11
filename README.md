# squawk
![Squawk logo](https://github.com/in03/squawk/blob/main/assets/squawk_logo.svg)


![GitHub](https://img.shields.io/github/license/in03/squawk) 
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![GitHub branch checks state](https://img.shields.io/github/checks-status/in03/squawk/main)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/in03/proxima/main.svg)](https://results.pre-commit.ci/latest/github/in03/squawk/main)

![GitHub last commit](https://img.shields.io/github/last-commit/in03/squawk)
![GitHub Repo stars](https://img.shields.io/github/stars/in03/squawk?style=social)

---

#### Automatic subtitles for DaVinci Resolve with OpenAI Whisper :sparkles:
Save time writing subtitles yourself and don't pay an online service to do it. Squawk generates subtitles for your videos in DaVinci Resolve! 
It renders audio of your timeline, transcribes it (speech-to-text) with Whisper, and automatically imports the subtitles into Resolve. Whisper can even translate other languages into English before transcribing.

> **Note**
>
> Currently only Resolve 18 is supported. Resolve 17 and older require Python 3.6, which is now EOL. Some dependencies have started dropping support for it. A Resolve 17 branch doesn't currently exist, and will not unless someone asks nicely for it or forks the project.

## Installation
Install with pipx
```
pipx install git+https://github.com/in03/squawk
```

## Commands

```
 _____ _____ _____ _____ _ _ _ _____ 
|   __|     |  |  |  _  | | | |  |  |
|__   |  |  |  |  |     | | | |    -|
|_____|__  _|_____|__|__|_____|__|__|
         |__|


Git build (cloned 🛠 ) '0141446'
Run squawk --help for a list of commands
editor@EMA:~$ squawk --help

✅  Checking settings...

 Usage: squawk [OPTIONS] COMMAND [ARGS]...

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────────────────╮
│ --install-completion   Install completion for the current shell.                                           │
│ --show-completion      Show completion for the current shell, to copy it or customize the installation.    │
│ --help                 Show this message and exit.                                                         | 
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────────────╮
│ config     Open user settings configuration file for editing                                               │
│ file       Transcribe a media file and import the transcription into Resolve.                              │
│ timeline   Transcribe a Resolve timeline and import the transcription into Resolve.                        | 
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

```

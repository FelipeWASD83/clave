# GameMaker project: where the code lives and how to run it

Checked on 2026-09-02. What is here as **procedure** always holds; what is
**machine state** needs to be rechecked.

## Check the machine first

Check whether GameMaker is installed: does `C:\ProgramData\GameMakerStudio2`
exist? Is the IDE under `Program Files`? Are there `.yyp` projects in the folder?

If it is **not** installed:

- There is no way to compile, run or take a screenshot of a GameMaker game here.
- Every GML delivery goes out **not compiled**, and that has to be said in the
  answer. No "I tested it" or "it is working".
- The verification that is possible is: function names checked against the
  manual (`checar-gml.py`) + a critical reading of the code.

If it is installed, check: the IDE is under `Program Files`, the runtimes and
`Igor.exe` are in `C:\ProgramData\GameMakerStudio2\Cache\runtimes\runtime-<version>\bin\igor\windows\x64\`,
and the license is in `%appdata%\GameMakerStudio2\<user_number>\licence.plist`.
From there you can compile without opening the IDE, and **then** the result can
be called tested.

## Structure of a project

A project is a folder with a `<name>.yyp` at the root, and one folder per
resource type (`objects/`, `sprites/`, `scripts/`, `rooms/`, `shaders/`,
`sounds/`, `fonts/`, `notes/`, `datafiles/`).

- `.yyp`: the project file, JSON. Lists the resources and the settings.
- `<type>/<name>/<name>.yy`: that resource's metadata, JSON.
- `<type>/<name>/*.gml`: the code.

Practical rules:

1. **Do not create or edit `.yy` and `.yyp` by hand** to add a new resource.
   The IDE generates GUIDs and cross-references; writing them by hand breaks
   the project in a way that is hard to diagnose. Editing `.gml` is safe;
   editing `.yy` only when there is no alternative, and telling the user.
2. **Each object event is a separate `.gml`**, named in the format
   `EventType_Number.gml` (`Create_0.gml`, `Step_0.gml`, `Draw_0.gml`,
   `Alarm_0.gml`...). **Do not deduce which event is which from the number**:
   the numbers for Step, Draw and Other don't follow the order they seem to.
   Open the object's `.yy`, which lists the events, or confirm in the manual at
   `GameMaker_Language/GML_Reference/Asset_Management/Objects/Object_Events/event_perform.htm`.
3. **Scripts** live in `scripts/<name>/<name>.gml` and can hold several named
   functions. The post-GMS 2.3 convention is `function function_name()`, not
   one file per function with `argument0`.
4. **Read the project before writing.** Which naming convention it uses
   (`obj_`, `spr_`, `scr_`?), whether it uses structs or `ds_*`, whether it has
   its own state system. Fit into what exists.

## Compile from the command line (when GameMaker is there)

The runtime's `Igor.exe` accepts, among others:

| Option | What it is for |
|---|---|
| `/project=<path to the .yyp>` | the project |
| `/uf=<user folder>` or `/lf=<licence.plist>` | license (mandatory) |
| `/rp=<runtime root>` | runtime to use |
| `/runtime=VM\|YYC` | build type (default VM) |
| `/config=<name>` | configuration (default `Default`) |
| `/of=<output file>` | generated executable |
| `/launch` | runs after compiling |

It requires having signed in to the IDE at least once.
Source: `Settings/Building_via_Command_Line.htm` in the manual.

## Git

A GameMaker project versions well: `.yyp`, `.yy` and `.gml` are text. What
should **not** go into git are the generated build and cache folders: confirm
the exact names in the real project before writing the `.gitignore`, instead of
copying a `.gitignore` from the internet.

The folder rule applies: one project = one folder at the root, git in every
project, commit only when the task is finished.

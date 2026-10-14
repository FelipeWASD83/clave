# Projeto GameMaker: onde o código vive e como rodar

Verificado em 02/09/2026. O que aqui é **procedimento** vale sempre; o que é
**estado da máquina** precisa ser reconferido.

## Conferir a máquina antes

Verificar se o GameMaker está instalado: existe `C:\ProgramData\GameMakerStudio2`?
Existe a IDE em `Program Files`? Há projetos `.yyp` na pasta?

Se **não** estiver instalado:

- Não há como compilar, rodar ou tirar screenshot de jogo GameMaker aqui.
- Toda entrega de GML sai **não compilada**, e isso tem que ser dito na
  resposta. Nada de "testei" ou "está funcionando".
- A verificação possível é: nomes de função conferidos no manual
  (`checar-gml.py`) + leitura crítica do código.

Se estiver instalado, conferir: a IDE fica em `Program Files`, os runtimes e
o `Igor.exe` em `C:\ProgramData\GameMakerStudio2\Cache\runtimes\runtime-<versão>\bin\igor\windows\x64\`,
e a licença em `%appdata%\GameMakerStudio2\<usuario_numero>\licence.plist`.
A partir daí dá pra compilar sem abrir a IDE, e **aí sim** o resultado pode ser
chamado de testado.

## Estrutura de um projeto

Um projeto é uma pasta com um `<nome>.yyp` na raiz, e uma pasta por tipo de
recurso (`objects/`, `sprites/`, `scripts/`, `rooms/`, `shaders/`, `sounds/`,
`fonts/`, `notes/`, `datafiles/`).

- `.yyp` — arquivo do projeto, JSON. Lista os recursos e as configurações.
- `<tipo>/<nome>/<nome>.yy` — metadados daquele recurso, JSON.
- `<tipo>/<nome>/*.gml` — o código.

Regras práticas:

1. **Não criar nem editar `.yy` e `.yyp` na mão** para adicionar recurso novo.
   A IDE gera GUIDs e referências cruzadas; escrever isso à mão quebra o
   projeto de um jeito difícil de diagnosticar. Editar `.gml` é seguro; editar
   `.yy` só quando não houver alternativa, e avisando o usuário.
2. **Cada evento de objeto é um `.gml` separado**, com nome no formato
   `TipoDoEvento_Numero.gml` (`Create_0.gml`, `Step_0.gml`, `Draw_0.gml`,
   `Alarm_0.gml`...). **Não deduzir qual evento é qual pelo número** — os
   números de Step, Draw e Other não seguem a ordem que parece. Abrir o `.yy`
   do objeto, que lista os eventos, ou confirmar no manual em
   `GameMaker_Language/GML_Reference/Asset_Management/Objects/Object_Events/event_perform.htm`.
3. **Scripts** ficam em `scripts/<nome>/<nome>.gml` e podem conter várias
   funções nomeadas. A convenção pós-GMS 2.3 é `function nome_da_funcao()`, não
   um arquivo por função com `argument0`.
4. **Ler o projeto antes de escrever.** Que convenção de nome ele usa
   (`obj_`, `spr_`, `scr_`?), se usa structs ou `ds_*`, se tem sistema próprio
   de estado. Encaixar no que existe.

## Compilar pela linha de comando (quando houver GameMaker)

O `Igor.exe` do runtime aceita, entre outros:

| Opção | Para quê |
|---|---|
| `/project=<caminho do .yyp>` | o projeto |
| `/uf=<pasta do usuário>` ou `/lf=<licence.plist>` | licença (obrigatório) |
| `/rp=<raiz do runtime>` | runtime a usar |
| `/runtime=VM\|YYC` | tipo de build (padrão VM) |
| `/config=<nome>` | configuração (padrão `Default`) |
| `/of=<arquivo de saída>` | executável gerado |
| `/launch` | roda depois de compilar |

Exige ter logado na IDE ao menos uma vez.
Fonte: `Settings/Building_via_Command_Line.htm` no manual.

## Git

Projeto GameMaker versiona bem: `.yyp`, `.yy` e `.gml` são texto. O que **não**
deve ir para o git são as pastas geradas de build e cache — confirmar os nomes
exatos no projeto real antes de escrever o `.gitignore`, em vez de copiar um
`.gitignore` de internet.

Vale a regra da pasta: um projeto = uma pasta na raiz, git em todo projeto,
commit só quando a tarefa termina.

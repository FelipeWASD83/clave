---
titulo: Permissões: o que o Claude faz sozinho
trilha: 3. Automação com o modo Code
ordem: 26
duracao: 6 min
resumo: Regras para liberar o que é seguro, bloquear o que nunca deve acontecer e ver o histórico de tudo.
---

O modo de permissão (Perguntar, Aceitar edições, Plano, Livre) vale para tudo de uma vez. As **regras** são mais finas: liberam ou bloqueiam uma ação específica.

## Três tipos de regra

| Regra | O que faz | Exemplo |
|---|---|---|
| **Nunca** | bloqueia, em qualquer modo | nunca mandar nada para o GitHub |
| **Sempre perguntar** | pede OK mesmo no modo Livre | sempre perguntar antes de mexer em planilha |
| **Fazer sem perguntar** | libera mesmo no modo Perguntar | pode rodar os testes sem perguntar |

Se duas regras se contradizem, **Nunca** vence **Sempre perguntar**, que vence **Fazer sem perguntar**.

## O jeito mais fácil de criar uma regra

Quando o Claude pedir permissão, clique em **Mais opções**:

- **Permitir nesta tarefa:** vale até essa resposta terminar.
- **Sempre nesta pasta…:** salva uma regra para aquela pasta.
- **Sempre, em todo o Clave…:** salva uma regra que vale em todas as pastas.

O Clave sugere a regra (por exemplo, `Bash(git status *)`) e você pode ajustar antes de salvar. No cartão de site do [navegador do Code](#/aprender/navegador), o próprio **Permitir** já vale até a resposta terminar, e **Mais opções** traz só as duas de **Sempre**.

## Como uma regra é escrita

O formato é o mesmo do Claude Code, então as regras servem nos dois:

- `Bash(npm test *)`: um [comando](#/aprender/glossario/comando) (o `*` vale "qualquer coisa").
- `Edit(docs/**)`: criar ou mudar arquivos dentro da pasta `docs`.
- `Read(*.pdf)`: ler arquivos PDF.
- `WebFetch(domain:exemplo.com)`: abrir páginas de um site. Numa regra **Nunca**, ela também impede o [navegador do Code](#/aprender/navegador) de usar esse site (abrir, ler, clicar, nada).
- `Navegador(exemplo.com)`: o navegador do Code naquele site; `Navegador(*.exemplo.com)` vale o site e os subdomínios (o asterisco só vale no começo). Em **Fazer sem perguntar**, ela tira o cartão do site, mas clicar e digitar continuam pedindo OK. `Navegador` sozinho ou `Navegador(*)` fazem o mesmo em todos os sites.
- `Navegador(clicar:exemplo.com)`: só uma ação do navegador naquele site. As ações são `abrir`, `ler`, `print`, `rolar`, `voltar`, `clicar` e `digitar`, ou em inglês `open`, `read`, `print`, `scroll`, `back`, `click` e `type`; `Navegador(digitar)` ou `Navegador(clicar:*)` valem em qualquer site. Só uma regra que diz a ação dispensa o OK de clicar e digitar. Exemplo: `Navegador(clicar:localhost)` em **Fazer sem perguntar** deixa ele clicar no site que você está testando no seu computador sem pedir OK. Uma palavra que não é ação (`Navegador(apagar:exemplo.com)`) ou os dois-pontos sem nada antes (`Navegador(:exemplo.com)`) não valem como regra.
- **A porta conta.** `Navegador(clicar:localhost:5173)` vale só na porta 5173; sem porta, vale em qualquer uma. `Navegador(*:8080)` vale para qualquer site na porta 8080.
- O site da regra é lido do mesmo jeito que o navegador lê o endereço. `EXEMPLO.com`, `exemplo.com.` (com ponto no fim) e outros jeitos disfarçados de escrever o mesmo endereço contam como `exemplo.com`, e um IP escrito de outro jeito (`127.1`) conta como o mesmo IP (`127.0.0.1`). Assim, ninguém escapa de uma regra **Nunca** mudando a escrita.
- `Fluxo`: os fluxos (só "Nunca" tem efeito; fluxo sempre pede OK).

As regras de uma pasta ficam no arquivo `.claude/settings.local.json` dela, o mesmo que o Claude Code usa.

## Proteções que continuam valendo

- **Arquivos e pastas protegidos** (Configurações > Modo Code), como `.env` e chaves: as ferramentas de arquivo nunca leem nem mudam.
- Comando que **apaga ou publica** algo pergunta mesmo com os comandos liberados, a não ser que a regra seja escrita para aquele comando.
- **Fluxo** sempre pede OK.
- No navegador do Code, campos de **senha**, de **código de acesso** e de **cartão** o Claude nunca preenche, nem com regra: quem digita é você. No modo **Plano**, ele não clica nem digita.

## Testar e conferir

Em **Permissões** (Configurações > Modo Code, ou digitando `/permissoes`), dá para:

- ver e apagar as regras;
- **testar** ("esse comando passaria?") sem rodar nada;
- ver o **histórico** de cada ação: o que foi feito sozinho, o que você permitiu, o que foi bloqueado e por quê.

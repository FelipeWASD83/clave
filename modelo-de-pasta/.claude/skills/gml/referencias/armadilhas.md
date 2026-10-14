# Armadilhas de GML

Erros que eu cometo por reflexo, cada um conferido no manual oficial em
02/09/2026 (canal `monthly`). Onde a fonte importa, o caminho da página está no
fim do item — dá pra reler com `python docgml.py ver <caminho>`.

Isto não é um resumo da linguagem. É a lista do que eu erro.

---

## 1. Funções que não existem mais (mas eu escrevo por reflexo)

| O que eu escrevo | O que existe hoje |
|---|---|
| `instance_create(x, y, obj)` | `instance_create_layer(x, y, layer, obj)` ou `instance_create_depth(x, y, depth, obj)` |
| `array_length_1d(a)` / `array_length_2d(a)` | `array_length(a)` — as antigas existem mas o manual as marca DEPRECATED, e `array_length_1d` erra acima de 32.000 entradas |
| `d3d_*` | nada: a família inteira sumiu do manual |
| `argument0`, `argument1` em script | funções nomeadas com parâmetros: `function nome(_a, _b)` |

O padrão aqui é sempre o mesmo: **conteúdo de GMS 1.x ainda domina a internet**.
Quando um trecho "parece" GameMaker mas não bate com o manual, quase sempre é
código de 2015.

## 2. Arrays passam por referência — copy-on-write acabou

Hoje, modificar um array dentro de uma função **modifica o array original**. O
antigo *Copy on Write* está marcado como deprecated no manual e só volta se a
opção "Enable Copy on Write behaviour for Arrays" for ligada em General Game
Options.

Consequência prática: **parar de escrever `array[@ i] = v` por reflexo**. Com
CoW desligado (o padrão), `array[i] = v` dentro de função já altera o original.
O `@` só é necessário se o projeto tiver a opção legada ligada — o que se
descobre olhando as opções do projeto, não chutando.

Cuidado: a página `Data_Types.htm` do próprio manual ainda descreve o
comportamento antigo ("will then become a copy of the original array"). **Duas
páginas do manual se contradizem.** Quando isso acontecer, vale a página
específica do assunto (`GML_Overview/Arrays.htm`) e as release notes, não a
página genérica.

`GameMaker_Language/GML_Overview/Arrays.htm`

## 3. Retorno de função não pode ficar à esquerda de uma atribuição

```gml
instance_nearest(x, y, obj).speed = 0;      // erro de compilação
(instance_nearest(x, y, obj)).speed = 0;    // funciona
var _inst = instance_nearest(x, y, obj);    // melhor
_inst.speed = 0;
```

`GameMaker_Language/GML_Overview/Runtime_Functions.htm`

## 4. Atribuição encadeada não existe

`a = b = c = 4;` não faz o que parece. Escrever uma linha por variável. (E
`:=` é aceito como sinônimo de `=`, mas ninguém usa — não introduzir.)

## 5. `#RRGGBB` e `$RRGGBB` não são o mesmo número

GML lê cor em BGR. `$2c8edd` **não** é `#2c8edd`; o equivalente é `#dd8e2c`. O
prefixo `#` existe justamente para aceitar cor no formato CSS. Errar isso
produz um jogo com as cores trocadas e nenhum erro de compilação.

Hexadecimal aceita `$abcd` e `0xabcd`; binário aceita `0b0110`.

`GameMaker_Language/GML_Overview/Data_Types.htm`

## 6. Grafia britânica

O manual documenta **só** `colour` — nenhuma das 3113 páginas usa `color`. As
duas grafias compilam, mas o índice desta skill só conhece a britânica (o
`checar-gml.py` trata a conversão). **Escrever na grafia do manual** e, dentro
de um projeto existente, seguir a grafia que o projeto já usa.

## 7. Booleano é um real disfarçado

Qualquer real **maior que 0.5** é `true`; `<= 0.5` é `false`. Sempre usar as
constantes `true`/`false` e nunca comparar com `1`/`0`.

`GameMaker_Language/GML_Overview/Data_Types.htm`

## 8. Handle inválido não é `undefined`

- Instância inválida: `noone` (que vale `-4`), **não** `-1`, **não** `undefined`.
- Qualquer outro handle (lista, buffer, surface, sprite...): `-1`.
- Índices são **reciclados**: destruir uma lista e criar outra pode devolver o
  mesmo número. Depois de destruir, zerar a variável (`-1` ou `noone`), senão
  ela passa a apontar para um recurso novo de outra pessoa.

`GameMaker_Language/GML_Overview/Data_Types.htm`

## 9. Structs: o lado direito dos `:` não enxerga o struct

```gml
mystruct = { a : 10, b : 10, c : a + b };   // erro: a e b são procurados fora
```

Tudo à direita dos dois-pontos é avaliado **no escopo de quem está criando o
struct** (a instância, por exemplo). Por isso `{ x : x, y : y }` funciona e
copia o `x`/`y` da instância — e por isso existe o atalho `{ a, b, c: 101 }`
para variável de mesmo nome.

Structs e arrays são **coletados pelo garbage collector**. `delete` só prioriza
a coleta, não é obrigatório.

`GameMaker_Language/GML_Overview/Structs.htm`

## 10. DS* não são coletados — structs e arrays são

`ds_list`, `ds_map`, `ds_grid`, `ds_stack`, `ds_queue` e `ds_priority` **precisam
de `*_destroy()` manual**, senão vazam memória. O próprio manual recomenda
preferir array e struct, que são coletados sozinhos.

Não sair convertendo `ds_*` de projeto existente para struct por causa disso —
ver a regra de postura no `SKILL.md`.

`GameMaker_Language/GML_Reference/Data_Structures/Data_Structures.htm`

## 11. Accessors: cada estrutura tem o seu símbolo

| Estrutura | Sintaxe |
|---|---|
| DS List | `lista[| indice]` |
| DS Map | `mapa[? chave]` |
| DS Grid | `grade[# x, y]` |
| Struct | `st[$ "nome"]` |
| Array (escrita direta, legado CoW) | `arr[@ i]` |

Fora do intervalo, list/map/grid devolvem `undefined` (checar com
`is_undefined`), não dão erro.

`GameMaker_Language/GML_Overview/Accessors.htm`

## 12. Nomes de variável

Começam com letra ou `_`, só alfanumérico e `_`, **máximo 64 caracteres**. Não
podem repetir o nome de um asset do projeto (a menos que qualificados com
`self.`/`global.`). Reservados e proibidos: `player_avatar_sprite`,
`player_avatar_url`, `player_id`, `player_local`, `player_name`, `player_type`,
`player_user_id`, `player_prefs`, `managed`.

Também existe uma lista de nomes proibidos dentro de struct:
`GameMaker_Language/GML_Overview/Struct_Forbidden_Variables.htm`

## 13. Template string existe — usar

```gml
show_debug_message($"vida: {hp}/{hp_max}");
```

Introduzida nas versões recentes (está no LTS 2026.0). Em projeto antigo, checar
a versão antes de usar; se for velho, cair para `string()` e concatenação.

## 14. Duas ortografias de escopo que eu troco

- Sem `var`, dentro de um evento, a variável é **de instância** e sobrevive ao
  evento. Com `var`, é **local** e morre no fim do evento/função.
- `other` dentro de `with` é quem chamou o `with`, não o "outro" genérico.
- `self` dentro de um struct é o struct, não a instância que o criou.

`GameMaker_Language/GML_Overview/Variables_And_Variable_Scope.htm`

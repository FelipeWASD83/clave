---
name: direcao-visual
description: Define a direção visual de um site ou app antes de escrever CSS - lê a biblioteca de referências, monta três direções de verdade diferentes e fecha uma (escolhe sozinha quando o usuário não definiu a estética ou delegou; deixa ele escolher quando ele pede ou o projeto é de cliente). Usar ao começar qualquer projeto web novo, ao redesenhar um existente, ou quando ele disser que algo ficou feio ou genérico.
---

# Direção visual antes do CSS

Não existe estética padrão aqui. Não aplicar por reflexo o visual "padrão de IA"
(fundo escuro com neon, glassmorphism, gradiente roxo, uma cor de destaque só,
fonte mono em tudo) nem repetir o visual de projetos anteriores só porque já foi usado.

Mas "sem estética padrão" não significa "sem direção" — sem direção o resultado
cai no default genérico de IA, que é justamente o que ele não quer. Então:
**decidir a direção explicitamente, por escrito, antes da primeira regra de
CSS.** Quem fecha a escolha está no passo 3.

## 0. Ler a biblioteca visual — obrigatório

Antes de qualquer coisa nesta skill, ler `.claude/referencias-visuais/CLAUDE.md`.
Ele define como escolher referência pelo tipo de projeto, como ler o print em
vez do link, e como transformar isso em decisões numéricas. Esta skill assume
essa leitura feita — as três direções do passo 2 saem de lá.

## 1. Levantar o que define o visual

Tirar do pedido e do projeto, antes de perguntar:

- Quem vai usar isso, e em que situação (celular na rua? monitor em casa?).
- É projeto pessoal dele, ferramenta interna, ou **de cliente**?
  Se for cliente, **a identidade do cliente manda** e as direções só variam
  dentro dela.
- Que sensação a coisa tem que passar em 2 segundos.
- Tem referência que ele já gostou? Print vale mais que dez adjetivos.

Perguntar só o **fato** que não dá para deduzir **e** trava o trabalho —
principalmente se é de cliente —, no máximo 3 perguntas. O resto (quantidade
de conteúdo, se vai ao ar, de onde vêm as imagens): supor o razoável, escrever
a suposição junto das direções e seguir. **Gosto não vira pergunta:** se ele
não disse, é escolha minha (passo 3).

## 2. Montar 3 direções distintas

Três direções **de verdade diferentes** — não três variações da mesma coisa com
outra cor. Cada uma em até 4 linhas:

```
NOME DA DIREÇÃO
Sensação: <o que passa>
Cor: <papel das cores, não só os hex>
Tipografia: <estilo e contraste entre título e corpo>
Movimento: <tem animação? qual o papel dela?>
Referência: <verbete da biblioteca + arquivo do print>
Decisões: <até 3 decisões numéricas puxadas daquele print>
```

Puxar referência de `.claude/referencias-visuais/CLAUDE.md`, escolhendo a seção
pela tabela do passo 1 de lá (tipo e frequência de uso decidem, não o gosto;
em projeto de cliente, a identidade dele vem na frente de tudo).
**Citar o arquivo do print**, não só o nome do site — e ter olhado o print, não
só o link. Se o usuário já mandou print, a referência dele tem prioridade.

## 3. Fechar a escolha

- **Ele pediu para escolher** ("me mostra opções", "quero escolher") →
  apresentar as três e esperar. CSS só depois da escolha (ou mistura) dele.
- **Projeto de cliente** → as três, dentro da identidade do cliente, vão para
  ele escolher: a decisão é dele junto com o cliente. A não ser que ele diga
  que eu escolho.
- **Nos outros casos** — projeto pessoal sem estética definida, "escolhe você",
  "escolhe tudo", "faz do jeito que achar melhor" → **eu fecho uma**, digo qual
  e por quê em até duas linhas, mostro as outras duas resumidas (para ele poder
  trocar) e sigo. Não devolver essa escolha como pergunta.

A direção fechada entra no plano da seção 5 das regras da pasta como decisão
tomada. Se ele delegou com todas as letras ("escolhe tudo", "faz do jeito que
achar melhor" e afins), não existe a parada do "pode ir?": contar a direção
em poucas linhas e seguir para o passo 4. Sem essa frase, o plano espera o
"pode ir" como qualquer tarefa não trivial — só não carrega escolha pendente.

## 4. Fechar o sistema antes de espalhar

Com a direção fechada, definir de uma vez e usar em tudo:

- Escala de espaçamento (4/8/12/16/24/32/48/64).
- Escala tipográfica (3 a 5 tamanhos, não doze).
- Paleta: fundo, superfície, texto forte, texto fraco, borda, ação, erro, sucesso.
- Raio de borda e sombra: **um** valor de cada por nível, não improvisado por componente.
- Duração de transição: uma rápida (150ms) e uma normal (300ms).

Escrever isso como variáveis CSS no topo do arquivo, com um comentário em
português dizendo o que cada grupo controla — assim ele consegue trocar uma cor
na mão sem entender o resto.

## 5. Regra anti-genérico

Se o resultado poderia ser o site de qualquer outra coisa só trocando o texto,
a direção falhou. Cada projeto precisa de pelo menos **um elemento que só faz
sentido nele** — pode ser o tratamento do título, uma ilustração, o jeito que a
lista se comporta, a textura do fundo. Um, bem feito, vale mais que cinco efeitos.

## 6. Peso é custo

Fonte externa, biblioteca de animação e shader entram só se pagarem o próprio
peso. Site de estúdio premiado carrega 8 MB porque o produto **é** a experiência.
Uma ferramenta que ele usa toda semana, não. Three.js/GSAP em projeto pequeno
entram no plano com o peso e o motivo escritos — nunca calados.

## 7. Fechar comparando com a referência

Direção fechada e CSS escrito, **não declarar pronto sem comparar**: capturar
o resultado em 1440×900 e colocar ao lado do print da referência, respondendo
as cinco perguntas do passo 4 de `.claude/referencias-visuais/CLAUDE.md`
(hierarquia, respiro, contraste de escala, papel da cor, elemento único).
Quem executa essa comparação é a skill `revisar-visual` — ela é manual, então
abrir `.claude/skills/revisar-visual/SKILL.md` e seguir os passos 2, 3.5 e 4
dela.

---
titulo: Acompanhar e travar o gasto (e 10 hábitos que economizam)
trilha: 5. Economizar crédito
ordem: 46
duracao: 8 min
resumo: Onde ver quanto você gastou, como ler os números, as travas que seguram o mês e a lista dos 10 hábitos desta trilha.
---

Economizar fica fácil quando você enxerga o gasto. O Clave soma o custo de cada resposta pelos preços oficiais e mostra isso em vários lugares, do detalhe de uma resposta ao mês inteiro. E tem travas para o mês não fugir do controle, mesmo num dia distraído.

## Onde olhar

| Onde | O que mostra |
|---|---|
| Embaixo de cada resposta | o modelo e quanto ela custou (se não aparecer, ligue em **Configurações > Aparência > Mostrar o custo de cada resposta**) |
| Embaixo da caixa de texto | a régua com o tamanho da conversa e quanto ela já custou |
| **/custo** | quanto esta conversa e o mês já gastaram |
| O tinteiro, no canto da barra da esquerda | quanto do teto do mês já foi usado e em que dia zera (clique para abrir o **Uso e gasto**) |
| **Seu uso**, na tela de conversa nova | tokens no total, dias seguidos, mapa de calor, modelo favorito, o gasto do mês, cada modelo nos últimos 7 dias e a projeção do mês |
| **Uso e gasto**, na barra da esquerda | o ciclo inteiro: por dia, por modelo e por conversa |
| **Preços e planos**, na barra da esquerda | o preço de cada modelo, a sua projeção e a conta **API ou assinatura?** |

A projeção olha o ritmo dos últimos 14 dias e diz quanto o mês deve fechar e, se você tem um teto, em que dia ele acaba. O painel **Seu uso** pode ser escondido no X (e volta em **Configurações > Aparência > Painel de uso no início**).

## Como ler o Uso e gasto

**Por modelo** tem estas colunas: **Pedidos**, **Entrada**, **Cache lido**, **Saída**, **Buscas** e **Custo**. O que cada uma costuma dizer:

| Se você vê | Provavelmente é | Lição |
|---|---|---|
| O Opus ou o Fable com a maior parte do custo, em tarefas simples | modelo caro fazendo trabalho de Haiku | [O modelo certo](#/aprender/modelo-certo-mais-barato) |
| **Saída** alta | respostas longas e muito raciocínio | [Raciocínio](#/aprender/raciocinio-sem-desperdicio) |
| **Entrada** alta perto do **Cache lido** | pausas em conversas longas, troca de modelo no meio, anexos grandes | [Conversas enxutas](#/aprender/conversas-enxutas) |
| Muitas **Buscas** | Web ligada onde não precisava (US$ 0,01 cada) | o hábito 7, no fim desta lição |
| **Pedidos** muito acima das mensagens que você mandou | passos do Code, etapas de fluxo e rotinas | [O modo Code](#/aprender/code-sem-desperdicio) |

**Por conversa** mostra as 30 que mais gastaram no ciclo (clique para abrir). Se uma rotina aparece sempre no topo, veja [Automatizar sem pagar a IA toda vez](#/aprender/automatizar-sem-ia).

**Gastos fora do Clave neste mês**: o Clave só enxerga o que ele mesmo gasta. Se a mesma conta da Anthropic é usada por outros programas, some aqui o que eles gastaram (o Console da Anthropic mostra) para o teto ficar certo.

## As travas

| Trava | Onde | Padrão | O que acontece |
|---|---|---|---|
| **Teto por mês** | Configurações > Limite de gasto | o valor escolhido na primeira vez que você abriu o Clave | avisos em 50%, 80% e 95%; no teto, para de responder até o mês virar, ou só avisa |
| **Dia em que o mês vira** | Configurações > Limite de gasto | dia 1 | use o dia em que o seu crédito renova (de 1 a 28) |
| **Teto por tarefa no modo Code** | Configurações > Limite de gasto | US$ 2 | pausa a tarefa; você manda "continue" para seguir |
| **Ações seguidas no modo Code** | Configurações > Limite de gasto | 60 | depois desse número de ações (ler, editar, rodar um comando) num envio, pausa; você manda "continue" ou clica em Continuar |
| **Teto por rodada** | no formulário de cada rotina | | a rodada para ao chegar nele |
| **Teto do fluxo** | no cartão do fluxo, antes de rodar | | o fluxo para se a soma passar dele |
| **Limite no Console da Anthropic** | um workspace com limite de gasto, e uma chave desse workspace | | uma trava que nem o Clave consegue passar |

Em **Quando chegar no teto**, prefira **Parar de responder até o mês virar**: com **Só avisar e continuar**, o aviso aparece, mas o gasto segue. Parado no teto, o Clave também não roda as rotinas. O aviso diz em que dia o mês zera; para seguir antes disso, aumente o teto em **Configurações > Limite de gasto**.

**Assina o Claude Max?** O plano dá crédito mensal na API (US$ 100 no Max 5x, US$ 200 no Max 20x). Pôr o teto nesse valor mostra, pela projeção, se o crédito do plano vai durar o mês. A lição [Sua chave da API](#/aprender/chave-da-api) explica como ativar esse crédito.

## Cinco minutos por semana

1. Abra **Uso e gasto** e leia a projeção do mês.
2. Olhe as 3 primeiras de **Por conversa**: valeram o que custaram?
3. Em **Por modelo**, confira se o modelo mais caro estava fazendo tarefas simples.
4. Em **Rotinas**, pergunte de cada uma: ainda precisa? Dá para virar um programa sem IA?
5. Ajuste o teto, se o mês mudou.

```experimentar
Estes são os meus gastos no Clave neste mês, copiados da página Uso e gasto:

[cole aqui as tabelas Por modelo e Por conversa]

Em no máximo 6 tópicos curtos, diga onde eu provavelmente estou gastando mais do que precisava e o que mudar. Use estas referências: o Haiku 5.5 custa uns 40 vezes menos que o Opus 5.5 por mensagem; cada busca na web custa US$ 0,01; uma conversa longa retomada depois de mais de 5 minutos paga a conversa inteira de novo.
```

## Os 10 hábitos que economizam

Esta é a trilha inteira numa lista. Volte nela de vez em quando.

1. **Comece no Haiku e suba só quando precisar.** Ele custa uns 40 vezes menos que o Opus; o conselheiro avisa quando a tarefa pede mais. [Veja mais](#/aprender/modelo-certo-mais-barato)
2. **Raciocínio no Baixo ou no Médio no dia a dia.** O pensamento é cobrado como texto escrito; Alto e acima só para o que é difícil. [Veja mais](#/aprender/raciocinio-sem-desperdicio)
3. **Peça respostas curtas.** "Em 5 linhas", "sem introdução": uns três quartos do preço de uma mensagem curta são o que o Claude escreve. [Veja mais](#/aprender/para-onde-vai-o-credito)
4. **Assunto novo, conversa nova.** E para continuar uma conversa longa depois de uma pausa, leve um /resumo para uma conversa nova em vez de voltar nela. [Veja mais](#/aprender/conversas-enxutas)
5. **Decida modelo, raciocínio e Web no começo da conversa.** Trocar no meio de uma conversa longa faz a próxima mensagem pagar tudo de novo.
6. **Edite a mensagem em vez de corrigir com outra.** A resposta errada sai do caminho e não é relida nas mensagens seguintes.
7. **Mande só o que importa e use /web off quando nada atual for necessário.** Uma página de PDF vale 1.500 a 3.000 tokens; uma busca custa o mesmo que umas 20 mensagens curtas no Haiku.
8. **No Code: diga o arquivo, peça o plano, teste em poucos e responda os cartões logo.** Menos passos e nenhuma releitura à toa. [Veja mais](#/aprender/code-sem-desperdicio)
9. **Tarefa repetida vira programa, não rotina.** O programa custa uma vez; a rotina, a cada rodada, para sempre. [Veja mais](#/aprender/automatizar-sem-ia)
10. **Deixe o teto do mês ligado e olhe o Uso e gasto toda semana.** Gasto que você vê é gasto que você controla.

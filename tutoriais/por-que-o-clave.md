---
titulo: Por que usar o Clave (e a API)
trilha: 1. Primeiros passos
ordem: 0
duracao: 4 min
resumo: Pagar pelo que usa, sem limite de 5 horas, com os seus dados no seu computador. E quando o app oficial é melhor.
---

O Clave conversa com o Claude pela [API](#/aprender/glossario/api), com a sua [chave](#/aprender/glossario/chave-da-api). Parece um detalhe técnico, mas muda muita coisa para quem usa.

## Você paga pelo que usa

A assinatura Pro do Claude custa US$ 20 por mês, use você muito ou pouco. Pela API, cada resposta custa o que gastou:

| Uso | Custo aproximado |
|---|---|
| Mil mensagens curtas no Haiku 5.5 | uns US$ 0,40 |
| Mil mensagens curtas no Sonnet 5.5 | uns US$ 7 |
| Uma pergunta ao ajudante das lições | uma fração de centavo |

(São estimativas sem raciocínio longo; com raciocínio a resposta fica mais cara.) O Clave mostra o custo **de cada resposta** e o total do mês na barra da esquerda. Quem usa a IA algumas vezes por dia gasta centavos.

## Sem "volte em 5 horas"

Os planos do app têm limite por janela de 5 horas e um limite semanal. Na API não existe nada disso: o limite é de pedidos por minuto, folgado para uma pessoa. Quem controla o gasto é você, com o **teto mensal** do Clave: chegou nele, ele para. Nada de susto na fatura.

## Seus dados ficam com você

- Por padrão, a Anthropic **não usa o que passa pela API para treinar modelos** e apaga do servidor dela em até 30 dias.
- As conversas, a [memória](#/aprender/memoria) e o histórico de gasto ficam **só no seu computador**.
- A chave fica guardada criptografada pelo Windows.
- O código do Clave é aberto: qualquer pessoa pode conferir o que ele faz.

## O modelo certo para cada coisa

Você escolhe o [modelo](#/aprender/modelos-e-raciocinio) em cada conversa: Haiku para o simples, Sonnet para o dia a dia, Opus para o difícil. Com os [fluxos](#/aprender/fluxos-e-agentes), os três trabalham juntos numa tarefa grande, e você vê o custo estimado antes de aprovar.

## Automação de verdade

No [modo Code](#/aprender/modo-code), o Claude trabalha numa pasta sua: organiza arquivos, monta planilhas, escreve scripts e roda comandos, sempre com o antes e o depois e o botão de desfazer. As [rotinas](#/aprender/rotinas) fazem ele trabalhar no horário, até com o Clave fechado. E o que você aprende aqui (CLAUDE.md, skills, agentes, comandos, plugins, regras de permissão) usa o mesmo formato do Claude Code.

## Já assina o Max?

O plano Max dá crédito mensal na API (US$ 100 no Max 5x, US$ 200 no Max 20x), e o Clave usa esse crédito. Veja como ativar na lição da [chave da API](#/aprender/chave-da-api).

## Quando o app oficial é melhor

Sem enrolação: se você quer o Claude **no celular** ou sincronizado entre vários aparelhos, o app oficial faz isso e o Clave não. E quem usa o Opus o dia inteiro, todo dia, pode gastar mais pela API do que pela assinatura. A página **Uso e gasto** mostra quanto você gastou por dia e por modelo: em um mês você sabe qual dos dois sai mais barato para o seu jeito de usar.

```experimentar
Quanto eu gastaria por mês se fizesse umas 20 perguntas curtas por dia no Haiku 5.5? E no Sonnet 5.5? Faça a conta passo a passo.
```

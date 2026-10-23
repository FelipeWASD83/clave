---
titulo: Rotinas: o Claude trabalhando no horário
trilha: 3. Automação com o modo Code
ordem: 27
duracao: 5 min
resumo: Um pedido salvo que roda sozinho todo dia, em alguns dias da semana ou a cada poucas horas.
---

Uma **rotina** é um pedido que o Claude faz sozinho no horário que você escolher. Exemplos:

- "Toda manhã, leia os arquivos novos da pasta Relatórios e me diga o que precisa da minha atenção."
- "Toda sexta às 17h, monte o resumo da semana a partir da planilha de vendas."
- "A cada 3 horas, confira se a planilha de pedidos tem linha sem preço."

## Criar

1. Barra da esquerda > **Rotinas** > **Nova rotina**.
2. Escreva o pedido **completo**, como se fosse para alguém que não pode te perguntar nada.
3. Escolha onde ela trabalha (no chat ou numa pasta), quando roda, o modelo e o **teto por rodada** (o máximo que ela pode gastar cada vez).
4. Clique em **Rodar agora** para testar antes de deixar no automático.

Cada rodada vira uma conversa na barra da esquerda ("Rotina: nome · data"), e uma notificação avisa quando ela termina.

## Rotina só faz o que você já liberou

Numa rotina ninguém está olhando, então ela **não pergunta nada**:

- ler arquivos dentro da pasta: pode;
- mudar arquivos, rodar comandos: só se houver uma [regra de permissão](#/aprender/permissoes) liberando;
- se precisar de um OK, ela **para** e conta o que precisaria (com a regra sugerida). Você cria a regra e roda de novo.

Rotina também não roda fluxo (ninguém estaria lá para aprovar o cartão do fluxo).

## Com o Clave fechado

Por padrão, a rotina roda com o Clave aberto. Marcando **Rodar mesmo com o Clave fechado**, o Clave cria uma tarefa no **Agendador de Tarefas do Windows** (pasta "Clave"), que roda a rotina sem abrir janela e avisa por notificação. O computador precisa estar ligado. Apagar a rotina (ou desmarcar a opção) tira a tarefa do Agendador.

Se o PC estava desligado no horário, a rotina não "acumula": ela roda no próximo horário.

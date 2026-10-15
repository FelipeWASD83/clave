---
titulo: Desfazer, backup e Git: a sua rede de segurança
trilha: 8. Usar com segurança
ordem: 72
duracao: 7 min
resumo: O que dá para voltar atrás no Clave, o que não dá, e como deixar tudo guardado antes de uma tarefa grande.
---

Errar faz parte, seu ou do Claude. O que importa é conseguir voltar. O Clave tem várias redes de segurança, e cada uma pega um tipo de erro:

| Rede | Quando ajuda | O limite |
|---|---|---|
| **Posso fazer assim?** | antes de começar: você vê o plano e decide | aparece só nas tarefas grandes |
| **Desfazer mudanças** | arquivos que o Claude criou ou editou numa resposta | não desfaz o que um comando fez |
| **Lixeira do Windows** | arquivo apagado pela aba Arquivos ou pelo Explorador | arquivo apagado por comando some de vez |
| **Git** | qualquer mudança na pasta, voltando a uma versão salva | só guarda o que você salvou numa versão |
| **GitHub** | computador quebrado, roubado ou formatado | só tem o que você enviou |
| **Backup do Clave** | conversas, projetos e histórico de gasto | anexos, memória e chave ficam de fora |

## Antes: o plano

Antes de mexer em muita coisa (criar ou mudar três arquivos ou mais, mover, renomear ou apagar arquivos, reorganizar uma pasta), o Claude mostra um cartão **Posso fazer assim?** com o plano e espera a sua resposta:

- **Pode ir**: ele executa, e as permissões continuam valendo como sempre;
- **Mudar o plano**: escreva no campo o que quer diferente e ele refaz o plano;
- **Não fazer**: ele para e pergunta o que você prefere.

É o melhor momento para pegar um erro, porque nada mudou ainda. Isso vale em qualquer modo, enquanto **Pedir OK antes de tarefas grandes** estiver ligado em Configurações > Modo Code (deixe ligado). Se ele foi direto e você queria ver antes, peça: "me mostre o plano antes de mudar qualquer coisa". O modo **Plano** vai além: ele só lê e propõe.

## Desfazer mudanças

Embaixo de cada resposta que criou ou editou arquivos aparece **Desfazer mudanças**. Ele volta os arquivos daquela resposta para como estavam antes dela: o que foi editado volta ao texto antigo, e o arquivo que ela criou some.

O que ele **não** volta é o que um [comando](#/aprender/glossario/comando) fez: mover, renomear, apagar, rodar um script, instalar um programa, mandar algo para a internet. O botão não alcança nada disso. Por isso o cartão de cada comando mostra o que vai rodar antes, e comando que apaga ou publica sempre pede o seu OK, até no modo **Livre**.

Detalhes que valem saber:

- Cada resposta tem o seu botão. Para voltar várias, desfaça da última para a primeira.
- Ele põe o arquivo de volta como estava antes da resposta. Se você mexeu no arquivo depois, essa sua mudança também vai embora.
- Com a tarefa ainda rodando, pare antes de desfazer.
- Quer ver o que mudou antes de decidir? Abra o arquivo no **Visualizador** (clique nele na aba **Arquivos** do [painel do Code](#/aprender/painel-do-code)) e clique em **Mudanças do Claude**: aparece o que o Claude mudou naquele arquivo nesta conversa.
- O botão continua na conversa mesmo depois de fechar o Clave. Apagar a conversa apaga junto a chance de desfazer.
- No chat, nada se perde: editar a sua mensagem ou gerar outra resposta cria uma versão nova, e as setas **< 1/2 >** trocam entre elas.

Quer poder voltar o que um comando vai fazer? Peça antes:

```experimentar-code
Antes de mover ou renomear qualquer coisa nesta pasta, salve num arquivo mudancas.csv a lista do que vai mudar (de onde e para onde) e crie um script que desfaça tudo usando essa lista. Só depois faça as mudanças.
```

## A Lixeira

- Arquivo apagado pelo Explorador do Windows, ou pela aba **Arquivos** do [painel do modo Code](#/aprender/painel-do-code), vai para a **Lixeira**. Para trazer de volta: abra a Lixeira (o ícone na área de trabalho), clique com o botão direito no arquivo e escolha **Restaurar**.
- Arquivo apagado por **comando** (como `Remove-Item` ou `del`) **não passa pela Lixeira**: some de vez. É por isso que esse tipo de comando sempre pede o seu OK. Leia o cartão com calma.
- Precisa que o Claude apague alguma coisa? Peça: "em vez de apagar, mande para a Lixeira" ou "mova para uma pasta chamada para-apagar, que eu confiro e apago depois".
- Pendrive e pasta de rede não têm Lixeira: o Explorador apaga de vez, e a aba **Arquivos** nem deixa apagar por ali.

## Git: o histórico da pasta

O Desfazer cobre uma resposta. O [Git](#/aprender/glossario/git) cobre semanas: ele guarda "fotos" da pasta ao longo do tempo (os [commits](#/aprender/glossario/commit)), e você volta para qualquer uma delas.

- Pastas criadas pelo [modelo de pasta](#/aprender/modelo-de-pasta) já começam com Git, se o Git estiver instalado no computador.
- A pasta `.git`, onde mora o histórico, já vem na lista de arquivos protegidos: as ferramentas de arquivo do Claude não mexem nela.
- Comando que joga mudanças fora (`git reset --hard`, `git clean`) ou que envia para a internet (`git push`) sempre pede o seu OK.

Antes de uma tarefa grande:

```experimentar-code
Antes de qualquer mudança, salve uma versão desta pasta no Git com a mensagem "antes da arrumação". Se a pasta ainda não usa Git, me explique o que é e ative primeiro. Me mostre os comandos antes de rodar.
```

Quando algo deu errado:

```experimentar-code
Mostre as últimas versões salvas desta pasta no Git e o que mudou em cada uma, em linguagem simples. Não mude nada. Depois me diga como voltar o arquivo que eu escolher para uma dessas versões.
```

A lição [Git e GitHub para quem nunca usou](#/aprender/github) explica com calma.

## GitHub: a cópia fora do computador

O Git guarda o histórico no próprio computador: se o computador quebrar, vai junto. O [GitHub](#/aprender/glossario/github) guarda uma cópia na internet, num repositório **privado** que só você vê. O Clave sempre pede o seu OK antes de enviar (`git push`).

Senhas, chaves e dados pessoais **não** vão para o GitHub, nem em repositório privado. Peça ao Claude um arquivo `.gitignore` (a lista do que o Git deixa de fora) com os arquivos de senha e chave. Veja [Senhas, chaves e dados pessoais](#/aprender/segredos-e-dados).

## O backup do Clave

Em Configurações > **Dados e backup**:

- **Baixar backup das conversas**: um arquivo com as conversas, os projetos e o histórico de gasto.
- **Importar backup**: traz tudo de volta, num computador novo, por exemplo.

Os anexos, a memória e a chave não vão no backup. Para guardar tudo, copie de vez em quando a pasta `dados` do Clave para um HD externo ou para a nuvem, com o Clave fechado. A chave e as senhas guardadas ali só abrem no mesmo usuário do Windows: num computador novo, cole a chave de novo em Configurações > Conta e chave.

Mais três coisas:

- Para guardar **uma** conversa, use o menu dela (os três pontinhos) > **Exportar em Markdown**, ou digite `/exportar` nela.
- **Apagar uma conversa não tem volta**, e desinstalar o Clave apaga todas. Baixe o backup antes (veja [Atualizar o Clave e fazer backup](#/aprender/atualizar-e-backup)).
- O arquivo de backup tem tudo o que você escreveu nas conversas: guarde num lugar seguro.

## Antes de uma tarefa grande

1. Salve uma versão no Git (ou peça uma cópia da pasta, com a data no nome).
2. Deixe o modo em **Perguntar** ou **Plano** e leia o cartão **Posso fazer assim?**.
3. Peça para fazer primeiro em poucos arquivos, para você conferir.
4. Para mover ou renomear, peça a lista do que vai mudar.
5. No fim, confira o resultado e salve outra versão.

Pronto: se algo der errado, você sabe qual rede usar. As regras que decidem o que o Claude faz sozinho estão em [Permissões](#/aprender/permissoes), e o resto da segurança do Clave em [Segurança e privacidade](#/aprender/seguranca-e-privacidade).

---
titulo: Atualizar o Clave e fazer backup
trilha: 4. Ir além
ordem: 35
duracao: 3 min
resumo: Como receber as versões novas e guardar uma cópia das suas conversas.
---

## Atualizar

O Clave procura versão nova uma vez por dia, quando abre. Se tiver, aparece o botão **Atualizar** no canto de baixo da barra da esquerda. Você também pode procurar na hora em **Configurações > Atualizações e sobre**.

Ao clicar em **Atualizar e reiniciar**:

1. ele mostra o que mudou na versão nova;
2. baixa a versão do GitHub e confere o pacote;
3. guarda a versão atual (se a nova não abrir, ele volta sozinho para a anterior);
4. reinicia.

As suas conversas, configurações, memórias e a chave **não são tocadas**: elas ficam na pasta `dados`, que a atualização não mexe.

## Backup das conversas

Em **Configurações > Dados e backup**:

- **Baixar backup das conversas**: um arquivo com as conversas, os projetos, as rotinas e o histórico de gasto.
- **Importar backup**: traz de volta (num computador novo, por exemplo).

Os arquivos anexados, a chave e a [memória](#/aprender/memoria) não vão no backup. A chave você cria de novo no Console; os anexos, mande de novo se precisar. A memória mora na pasta `dados\memoria`: a cópia da pasta `dados`, logo abaixo, leva ela junto.

Para não perder nada, guarde também uma cópia da pasta `dados` do Clave num HD externo ou na nuvem de vez em quando (com o Clave fechado).

E os arquivos do seu trabalho, nas pastas do modo Code? Isso é outra história: veja [Desfazer, backup e Git: a sua rede de segurança](#/aprender/rede-de-seguranca).

## Sair da conta e desinstalar

Em **Configurações > Atualizações e sobre**, embaixo:

- **Sair da conta**: apaga a chave da API, as senhas salvas (e-mail, GitHub, conectores) e os dados do navegador do Code (logins e cookies dos sites), volta todas as configurações ao padrão e desliga as rotinas. As conversas, os projetos e a memória ficam. Depois aparecem a apresentação e os tours de novo, como na primeira vez. Serve para passar o computador para outra pessoa ou começar do zero com outra chave.
- **Desinstalar**: o Clave fecha e apaga a pasta dele (com as conversas, que moram lá dentro), os atalhos e as tarefas das rotinas no Agendador do Windows. Não dá para desfazer: se quiser guardar as conversas, baixe o backup antes.

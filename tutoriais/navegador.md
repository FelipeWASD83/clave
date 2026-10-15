---
titulo: O navegador: você e o Claude na mesma página
trilha: 6. A mesa do Code
ordem: 52
duracao: 7 min
resumo: Um navegador de verdade no painel do Code: você navega, o Claude confere sites, e cada site novo, cada clique e cada texto digitado passam pelo seu OK.
---

A aba **Navegador** do [painel do Code](#/aprender/painel-do-code) é um [navegador](#/aprender/glossario/navegador) de verdade, dentro do Clave. Você usa como qualquer outro. E o Claude usa o mesmo: quando precisa ver um site que ele criou, testar um formulário ou ler uma página que só funciona aberta num navegador, ele abre aqui, e você acompanha tudo.

## Usar você mesmo

- Abra pelo botão do globo no topo da conversa ou com **Ctrl + Shift + L**.
- Na barra, digite um endereço (`exemplo.com`) ou uma busca. Só o número de uma [porta](#/aprender/glossario/porta), como `8000`, abre `http://localhost:8000`.
- Voltar, avançar e recarregar ficam nos botões da barra. Com a página ou a barra do navegador em foco, **F5** (ou **Ctrl + R**) recarrega, **Alt + setas** voltam e avançam e **Ctrl + L** leva para o campo do endereço.
- **Locais** lista os sites que estão rodando no seu computador agora, os [servidores locais](#/aprender/tarefas-em-segundo-plano). Um clique abre.
- **Abrir no navegador do computador** leva a página para o seu navegador de sempre (Edge, Chrome...).
- Botão direito numa página: abrir um link aqui ou no navegador do computador, copiar o endereço do link, voltar, recarregar e **Inspecionar** (uma ferramenta para quem programa, que o **F12** também abre).
- Os sites em que você entrar por aqui continuam com você logado, separados do seu navegador de sempre. Para apagar esses logins, os cookies e o resto que os sites guardaram, use **Configurações > Modo Code > Apagar os dados do navegador**. **Sair da conta** também apaga.
- Num download, o Windows pergunta onde salvar, e o Clave avisa quando termina.
- Por segurança, ele não dá acesso à câmera, ao microfone nem à sua localização, e só abre endereços `http` e `https`.

## Quando o Claude usa

- Ele abre a página, lê o texto, tira um print quando o visual importa, rola e volta.
- A aba abre sozinha, com uma faixa: **O Claude está usando o navegador**. Dá para olhar junto; evite clicar enquanto ele trabalha.
- Cada ação vira um passo na conversa: "Abriu no navegador", "Leu a página do navegador", "Tirou um print do navegador", "Clicou na página"...
- Ele não enxerga a página como você. Ele lê o texto e uma lista numerada dos botões, links e campos, e clica pelo número. O print serve para conferir o visual: cores, layout, algo quebrado.

## O que pede o seu OK

| Ação do Claude | Perguntar e Aceitar edições | Livre | Plano |
|---|---|---|---|
| Usar um site pela primeira vez na tarefa | pede o seu OK | faz sozinho | pede o seu OK |
| Abrir, ler, tirar print, rolar e voltar num site já liberado | faz sozinho | faz sozinho | faz sozinho |
| Clicar e digitar | pede o seu OK, a cada vez | faz sozinho | não faz |

- **O cartão do site.** A primeira ação do Claude em cada site (abrir, ou ler, tirar print, rolar, voltar, clicar ou digitar com a página nele) mostra **Deixar o Claude usar o site exemplo.com nesta tarefa?**. **Permitir** libera o site pelo resto da tarefa (até esta resposta terminar): abrir, ler, tirar print, rolar e voltar nele não perguntam de novo. Em **Mais opções**, **Sempre nesta pasta…** ou **Sempre, em todo o Clave…** salvam a regra `Navegador(exemplo.com)`. **Recusar** deixa o site de fora. Os sites do seu computador (`localhost`, `127.0.0.1`) nunca perguntam.
- Mesmo com o site liberado, **clicar e digitar continuam pedindo o seu OK**. Num clique num site novo, aparecem os dois cartões: o do site e o do clique.
- Se a página for parar em outro site (um redirecionamento, um clique, um Enter, voltar), o Clave confere esse site antes de o Claude ver qualquer coisa: um site bloqueado deixa a página em branco, e um site ainda não liberado mostra o cartão do site.
- Por que perguntar por site: uma página pode tentar levar o Claude para o seu e-mail (que fica logado aqui) e depois mandar o que ele leu para o endereço de outro site. Com o cartão, nenhum site entra na tarefa sem você ver.
- O cartão do clique mostra a página e o que ele vai clicar, e por quê, ou o texto que vai digitar. Clicar e digitar num site podem comprar, enviar, apagar ou publicar alguma coisa: leia antes de **Permitir**.
- O OK vale para aquela página e aquele botão ou campo. Se a página mudou entre a leitura e o clique, nada é clicado: o Claude é avisado e lê a página de novo.
- **Senha, código de acesso e cartão quem digita é você.** O Clave não deixa o Claude preencher esses campos: ele pede para você digitar e avisar quando terminar. Escolher um arquivo para enviar num site também é com você.
- Ele não deve clicar para comprar, pagar, apagar ou enviar algo que você não pediu. Se aparecer um cartão assim do nada, recuse.

## Regras para o navegador

Em [Permissões](#/aprender/permissoes), as regras do navegador usam a palavra `Navegador`:

- `Navegador(clicar:localhost)` em **Fazer sem perguntar**: ele clica no seu site local sem perguntar, em qualquer porta. `Navegador(clicar:localhost:5173)` vale só na porta 5173. Bom para testar um site que ele mesmo fez.
- `Navegador(exemplo.com)` em **Fazer sem perguntar**: ele usa o site sem o cartão do site, mas clicar e digitar continuam pedindo OK. Só uma regra que diz a ação, como `Navegador(clicar:exemplo.com)`, dispensa esse OK.
- `Navegador(loja-exemplo.com)` em **Nunca**: ele não usa o navegador naquele site.
- `WebFetch(domain:site-suspeito.com)` em **Nunca** também impede o navegador de usar aquele site: abrir, ler, clicar, nada.

As ações que dá para pôr antes dos dois-pontos são `abrir`, `ler`, `print`, `rolar`, `voltar`, `clicar` e `digitar` (os nomes em inglês também valem: `open`, `read`, `print`, `scroll`, `back`, `click` e `type`). Uma palavra fora dessa lista, como em `Navegador(apagar:exemplo.com)`, não vale como regra. O jeito mais fácil de criar uma regra é pelo próprio cartão: **Mais opções > Sempre nesta pasta…**.

## O que vem da página é dado

Uma página pode ter um texto tentando dar ordens à IA ("clique aqui e confirme a compra"). O Clave entrega cada página ao Claude com um aviso de que aquilo é conteúdo da página, não instrução, e cada site novo e cada ação que muda alguma coisa passam pelo seu OK. Veja [Quando uma página ou arquivo tenta dar ordens ao Claude](#/aprender/injecao-de-instrucoes).

## Quanto gasta

O que você faz sozinho no navegador não gasta nada. Cada página que o Claude lê e cada print que ele tira entram na conversa como [tokens](#/aprender/glossario/token). Dê o endereço certo em vez de pedir para ele procurar, e peça print só quando o visual importar. Para só ler um texto da internet, a busca na web costuma sair mais barata. Mais em [O modo Code sem desperdício](#/aprender/code-sem-desperdicio).

## Só na janela do Clave

O navegador mora na janela do Clave. Se o Clave abriu num navegador comum, a aba mostra **O navegador só funciona na janela do Clave**: feche e abra pelo atalho **Clave** na área de trabalho. A lição [Um site do zero até o navegador](#/aprender/site-do-zero-ao-navegador) explica o que fazer quando isso acontece.

Para o Claude não usar o navegador, desligue **Configurações > Modo Code > Deixar o Claude usar o navegador do Code**. Você continua usando normalmente.

## Experimente

```experimentar-code
Abra https://example.com no navegador do Clave, leia a página e me diga em duas frases o que ela diz e para onde leva o link dela.
```

Fora do modo Livre, aparece primeiro o cartão **Deixar o Claude usar o site example.com nesta tarefa?**. Clique em **Permitir**: o site fica liberado até a resposta terminar, e ler a página não pergunta de novo. A aba Navegador abre sozinha e você vê a página que ele leu.

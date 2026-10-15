---
titulo: Para estudar
trilha: 9. Receitas por área
ordem: 80
duracao: consulta
resumo: Resumos, flashcards, perguntas de treino, explicações simples e um plano de estudo, cada um com o modelo mais barato que dá conta.
---

Pedidos prontos para estudar com o Claude. Clique em **Mandar para uma conversa nova**: o pedido vai para a caixa de texto, e você troca o que está entre colchetes antes de enviar.

Cada receita diz o que o Claude vai fazer, o [modelo](#/aprender/glossario/modelo) que basta (o mais barato que funciona) e quando outra ferramenta do Clave resolve melhor. O Clave começa no **Haiku 5.5**, o mais barato, e ele dá conta de quase tudo aqui. Quando a tarefa pede mais, o conselheiro de modelo avisa (veja [O modelo certo pelo menor preço](#/aprender/modelo-certo-mais-barato)).

| Receita | Onde | Modelo |
|---|---|---|
| Resumo de um texto | chat | Haiku (Sonnet para material longo e difícil) |
| Flashcards numa planilha | chat | Haiku |
| Perguntas de treino | chat | Haiku |
| Explicar como para uma criança | chat | Haiku, sem pensar |
| Plano de estudo numa linha do tempo | chat, com widget | Haiku |
| Corrigir a sua redação | chat | Haiku (Sonnet para um comentário mais fundo) |
| Pesquisa para um trabalho | chat ou fluxo | Haiku |
| Uma revisão por dia | rotina | Haiku |

## 1. Resumo de um texto ou capítulo

Anexe o PDF (ou fotos das páginas) e mande:

```experimentar
Resuma o texto que eu anexei para eu estudar para a prova. Quero: as 5 ideias principais, uma frase para cada; os termos novos, com uma explicação curta; e 3 perguntas que um professor faria sobre ele. Use só o que está no texto e me avise se alguma parte ficou confusa.
```

- **O que ele faz:** lê o anexo inteiro e devolve o resumo no formato pedido. O "use só o que está no texto" importa: assim ele avisa quando o texto não diz alguma coisa, em vez de completar de cabeça.
- **Modelo:** o Haiku basta para um capítulo. Material longo e difícil (um artigo científico, um livro inteiro) vai melhor no Sonnet, e o conselheiro costuma sugerir a troca.
- **Bom saber:** o anexo é relido a cada mensagem da conversa. Mande só o capítulo que vai estudar e comece uma conversa nova para o próximo (veja [Conversas enxutas](#/aprender/conversas-enxutas)). E quando a conversa passa de 100 mil [tokens](#/aprender/glossario/token) (um livro inteiro passa disso fácil), o Haiku cobra 5 vezes o preço normal naquela resposta.

## 2. Flashcards numa planilha

```experimentar
Crie uma planilha de flashcards sobre o sistema digestório, nível ensino médio. Colunas: Frente (a pergunta), Verso (a resposta, em no máximo duas linhas) e Tema. Faça 30 cartões, do mais fácil para o mais difícil.
```

- **O que ele faz:** cria a [planilha](#/aprender/glossario/planilha) do Excel e mostra um cartão com **Baixar** e **Abrir**. Anexou o seu material? Diga "use só o texto anexado" e os cartões saem do que o seu professor passou.
- **Modelo:** o Haiku basta.
- **Melhor ferramenta:** quer levar os cartões para um app de flashcards que importa CSV (como o Anki)? Abra a planilha no Excel e salve como CSV. Quer treinar na própria tela? Peça "uma página HTML de flashcards que vira o cartão quando eu clico": ela abre na **Prévia**, ao lado da conversa (veja [Criar páginas e pequenos apps](#/aprender/paginas-e-apps)).

## 3. Perguntas de treino

```experimentar
Quero treinar para uma prova de biologia sobre a célula, nível ensino médio. Faça uma pergunta por vez, de múltipla escolha, com 4 alternativas. Espere a minha resposta, diga se acertei, explique o porquê em duas linhas e só então passe para a próxima. Depois de 10 perguntas, me diga em que assunto eu preciso estudar mais.
```

- **O que ele faz:** vira um professor particular que corrige na hora e, no fim, aponta os seus pontos fracos.
- **Modelo:** o Haiku basta. Exercício com conta (matemática, física, química) erra menos com o [raciocínio](#/aprender/glossario/raciocinio) em **Médio** ou mais: pensar antes ajuda nas contas.
- **Melhor ferramenta:** prefere um simulado para fazer no papel? Peça "20 questões numa planilha, com o gabarito em outra aba".

## 4. Explicar como para uma criança

```experimentar
Explique o que é inflação como se eu tivesse 10 anos. Use um exemplo do dia a dia, no máximo 6 frases, e termine com uma pergunta para ver se eu entendi.
```

- **O que ele faz:** troca o jargão por uma comparação simples. Entendeu? Peça "agora explique de novo, como para um adulto que vai fazer prova", e o nível sobe aos poucos.
- **Modelo:** o Haiku, sem pensar: no segundo botão da caixa de texto, desmarque **Pensar antes de responder**. A resposta sai mais rápida e mais barata, e para uma explicação curta não faz falta.
- **Melhor ferramenta:** se você sempre quer explicações assim, escreva isso uma vez em **Configurações > Personalização** (veja [Ensine o Claude sobre você](#/aprender/sobre-voce-e-estilos)).

## 5. Plano de estudo numa linha do tempo

```experimentar
Tenho prova de história em 4 semanas e posso estudar 1 hora por dia, de segunda a sexta. Os assuntos são: Revolução Industrial, Revolução Francesa, Independência dos Estados Unidos e Era Napoleônica. Monte um plano com uma revisão no fim de cada semana e um dia leve antes da prova, e mostre o plano numa linha do tempo.
```

- **O que ele faz:** distribui os assuntos pelos dias e desenha uma linha do tempo na conversa. Esse cartão é um **widget**: um desenho que o Claude monta quando ajuda mais que texto. Os widgets vêm ligados (o interruptor fica em **Configurações > Recursos > Widgets**).
- **Modelo:** o Haiku basta.
- **Melhor ferramenta:** quer marcar o que já estudou? Peça também "o mesmo plano numa planilha, uma linha por dia, com uma coluna Feito".

## 6. Corrigir a sua redação (sem escrever por você)

```experimentar
Corrija a minha redação abaixo, mas não reescreva por mim. Aponte os erros de português, as frases confusas e onde o argumento ficou fraco, citando o trecho de cada problema. No fim, me dê 3 dicas para a próxima.

Redação: [cole aqui]
```

- **O que ele faz:** lista cada problema com o trecho, e quem reescreve é você. É assim que se aprende (e é o que a maioria das escolas aceita: siga as regras da sua sobre IA).
- **Modelo:** o Haiku basta para gramática e clareza. Para um comentário mais fundo sobre argumento e estrutura, o Sonnet vai melhor.
- **Melhor ferramenta:** quer só o texto corrigido, sem a aula? O comando `/escrita:revisar` seguido do texto corrige gramática e clareza sem mudar o sentido (veja [Plugins e comandos de barra](#/aprender/plugins-e-comandos)).

## 7. Pesquisa para um trabalho, com fontes

```experimentar
Estou fazendo um trabalho escolar sobre energia solar. Pesquise na web e me traga: um resumo do assunto em 10 linhas, 5 fatos importantes com a fonte de cada um e 3 sites confiáveis para eu ler. Diga a data das informações e avise onde as fontes discordam.
```

- **O que ele faz:** pesquisa na web (a busca vem ligada), lê as páginas e cita as fontes. Cada busca custa US$ 0,01, além dos tokens das páginas lidas.
- **Modelo:** o Haiku basta.
- **Melhor ferramenta:** assunto grande? Digite `/fluxo` e escolha **Pesquisa profunda**: três Haiku pesquisam ângulos diferentes ao mesmo tempo e um Sonnet junta tudo com as fontes. Ele mostra a estimativa de custo e só roda depois do seu OK (veja [Fluxos](#/aprender/fluxos-e-agentes)).
- **Cuidado:** o Claude pode errar e até inventar uma fonte (isso se chama [alucinação](#/aprender/glossario/alucinacao)). Abra os links antes de citar, e escreva o trabalho você mesmo.

## 8. Uma revisão por dia, sozinha

Uma [rotina](#/aprender/rotinas) faz um pedido no horário que você escolher, sem você abrir nada.

1. Na barra da esquerda, **Rotinas** > **Nova rotina**.
2. Em **O que fazer**, escreva o pedido completo, com os assuntos dentro dele:

   ```
   Sou estudante do ensino médio. Me faça 5 perguntas curtas de revisão, uma de cada assunto abaixo, e coloque as respostas no fim, depois de uma linha escrita "Respostas". Assuntos: célula, fotossíntese, Revolução Francesa, equação do 1º grau, figuras de linguagem.
   ```

3. Em **Quando**, escolha **Todo dia** e a hora. Em **Modelo**, escolha **Haiku 5.5**. Em **Teto por rodada**, ponha um valor baixo, como US$ 0,05.
4. Clique em **Rodar agora** para testar.

- **O que ele faz:** cada rodada vira uma conversa na barra da esquerda, e uma notificação avisa quando fica pronta.
- **Modelo:** o Haiku basta. Uma rodada dessas costuma custar menos de um centavo de dólar (é uma estimativa).
- **Bom saber:** a rotina não lê as suas outras conversas. Tudo o que ela precisa saber (aqui, os assuntos) vai no próprio pedido: troque a lista quando a matéria mudar.

## Dicas para estudar com o Claude

- **Um projeto por matéria:** instruções ("sou do 2º ano, explique com exemplos do dia a dia") e o material da matéria como arquivos. Veja [Projetos](#/aprender/projetos).
- **Mudou de matéria, conversa nova:** fica mais barato e ele se confunde menos.
- **Pergunte "como você chegou nisso?"** quando uma resposta parecer estranha.
- **Ele ajuda a aprender, não substitui o professor:** leve para a aula as dúvidas que sobrarem.

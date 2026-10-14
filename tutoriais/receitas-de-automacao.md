---
titulo: Receitas de automação para o dia a dia
trilha: 3. Automação com o modo Code
ordem: 23
duracao: consulta
resumo: Pedidos prontos para fotos, PDFs, documentos, relatórios e tarefas que rodam sozinhas.
---

Pedidos prontos para copiar. Em todos, escolha a pasta certa no modo Code e mantenha a permissão em **Perguntar** até pegar confiança.

Algumas receitas precisam de programas extras (por exemplo, uma biblioteca do Python para mexer em PDFs ou fotos). Quando for o caso, o Claude explica o que é e pede o seu OK antes de instalar.

## Fotos e imagens

```experimentar-code
Renomeie as fotos desta pasta com a data em que foram tiradas, no formato 2026-10-14_001.jpg. Antes, me mostre como ficariam os 5 primeiros nomes.
```

```experimentar-code
Crie uma cópia de todas as fotos desta pasta em tamanho menor (no máximo 1600 pixels de largura), numa subpasta chamada "para-whatsapp".
```

## PDFs e documentos

```experimentar-code
Junte todos os PDFs desta pasta num PDF só, em ordem alfabética, chamado documentos-juntos.pdf.
```

```experimentar-code
Leia os PDFs de notas fiscais desta pasta e monte uma planilha com data, fornecedor e valor de cada uma.
```

## Relatórios

```experimentar-code
Leia as planilhas desta pasta e escreva um relatório.md com os principais números do mês, comparando com o mês anterior, em linguagem simples.
```

## Arquivos e pastas

```experimentar-code
Ache arquivos repetidos nesta pasta (mesmo conteúdo, nomes diferentes) e me mostre a lista. Não apague nada.
```

```experimentar-code
Crie a estrutura de pastas para organizar os documentos da minha casa: contas, saúde, carro, escola das crianças e impostos, cada uma com subpastas por ano.
```

## Tarefas que rodam sozinhas

O Windows tem o **Agendador de Tarefas**, que roda um script em horários definidos. O Claude configura para você:

```experimentar-code
Crie um script que copie a pasta Documentos para o meu HD externo (letra E:) toda sexta às 20h, usando o Agendador de Tarefas. Me explique antes o que vai ser criado e como desligar.
```

## Dicas para automações que duram

- Peça sempre um **script** (arquivo .ps1 ou .py) em vez de uma ação de uma vez só: dá para rodar de novo.
- Peça para ele **escrever um LEIA-ME** explicando o que o script faz e como usar.
- Teste numa **cópia** da pasta antes de rodar nos arquivos de verdade.

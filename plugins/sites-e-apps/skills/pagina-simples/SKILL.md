---
name: pagina-simples
description: Use para criar uma página ou um pequeno app que roda no navegador (calculadora, lista, formulário, página de apresentação), num arquivo HTML só, que funciona no celular e no computador.
---

# Página simples

## Antes de escrever
- Entenda para quem é e o que a pessoa precisa fazer na página. Escolha um visual que combine com isso (uma página de padaria não parece um painel de banco). Sem pedido de estilo, escolha você e diga a escolha em uma linha.
- Num projeto maior (várias páginas, dados, login), avise que vale uma pasta organizada em vez de um arquivo só.

## Como fazer
- Um `index.html` com o CSS e o JavaScript dentro. Sem biblioteca da internet, a não ser que ela evite muito trabalho; se usar, diga qual e por quê.
- Funciona no celular: `<meta name="viewport" content="width=device-width, initial-scale=1">`, layout que se ajusta, botões com área de toque de pelo menos 44 px.
- Acessível: textos com contraste, `alt` nas imagens, rótulo em todo campo de formulário, dá para usar com o teclado.
- Dados que a pessoa digita ficam no próprio navegador (`localStorage`) e nada vai para a internet sem ela saber.
- Cores e tamanhos em variáveis CSS no topo, com comentário em português, para a pessoa conseguir trocar uma cor.

## Entregar
- No chat: um bloco ```html com a página inteira (a pessoa vê a prévia ao lado).
- No modo Code: salve o arquivo e ofereça abrir com `excel_abrir` (abre no navegador padrão).
- Antes de dizer que acabou, passe pela skill `sites-e-apps:checklist-web`.
- Explique como usar a página, não como o código funciona.

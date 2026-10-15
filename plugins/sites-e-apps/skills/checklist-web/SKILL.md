---
name: checklist-web
description: Use antes de dizer que uma página ou site está pronto. Confere celular, telas grandes, contraste, links, formulários, erros no console e peso das imagens.
---

# Checklist antes de dizer "pronto"

Confira cada item e diga quais você conferiu de verdade e quais não deu para conferir.

**Funciona**
- [ ] Abre sem erro no console do navegador.
- [ ] Todos os links e botões levam aonde dizem. Nenhum `href="#"` esquecido.
- [ ] Formulário: campos obrigatórios avisam, mensagem de sucesso e de erro aparecem.

**Em qualquer tela**
- [ ] Celular (390 px de largura): nada corta, nada rola para o lado, texto legível sem zoom.
- [ ] Notebook (1440 px) e monitor largo (2560 px ou mais): o conteúdo não fica esticado nem perdido num canto.
- [ ] Tela em pé (1080 × 1920): o layout ainda faz sentido.

**Dá para ler e usar**
- [ ] Contraste do texto com o fundo de pelo menos 4,5:1 (texto pequeno).
- [ ] Imagens com `alt`; campos com rótulo; dá para navegar com Tab.
- [ ] Título da aba (`<title>`) e descrição (`<meta name="description">`) certos; ícone da aba.

**Leve**
- [ ] Imagens no tamanho em que aparecem (nada de foto de 5 MB num quadradinho), em `.webp` ou `.jpg`.
- [ ] Sem senha, chave ou token no código da página: tudo que está no HTML qualquer um vê.

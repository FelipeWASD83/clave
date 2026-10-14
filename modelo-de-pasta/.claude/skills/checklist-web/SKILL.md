---
name: checklist-web
description: Checklist do que precisa estar pronto antes de dizer que um site ou app web está funcionando. Usar sempre antes de declarar concluída qualquer entrega de HTML/CSS/JS, e ao revisar um projeto web existente.
---

# Checklist — só declarar pronto depois disto

O usuário muitas vezes não consegue auditar o código para descobrir o que ficou pela metade.
Se eu disser "pronto" com um handler vazio, ele só descobre quando o app quebrar
na frente dele. Por isso: passar por esta lista **antes** de dizer que acabou, e
reportar item que falhou em vez de esconder.

Não é para colar a lista inteira na resposta. É para conferir e citar só o que
falhou ou o que foi decidido não fazer.

## Estados — o que mais falta

- [ ] **Vazio**: lista sem itens, busca sem resultado, primeiro acesso.
      Mostra uma mensagem, não uma área em branco.
- [ ] **Carregando**: qualquer coisa que demore mostra spinner, skeleton ou texto.
- [ ] **Erro**: fetch que falha, JSON inválido, API fora do ar, permissão negada
      (câmera, microfone, arquivo). Mostra o que aconteceu e o que fazer.
- [ ] **Sucesso**: a ação confirma que deu certo — não fica igual a antes.
- [ ] Botão que dispara ação lenta fica desabilitado enquanto roda, para não
      disparar duas vezes.

## Funcionalidade

- [ ] Nenhum handler vazio, nenhum `TODO`, nenhuma função que retorna
      valor fixo fingindo que funciona.
- [ ] Todo botão, link e campo visível faz alguma coisa. Se é decorativo, não
      parece clicável.
- [ ] Dado do usuário sobrevive a um F5, ou está avisado que não sobrevive.
- [ ] Entrada inválida não quebra: campo vazio, texto onde espera número,
      número negativo, texto gigante, caractere acentuado e emoji.
- [ ] **Console limpo**: zero erro. Warning conhecido e inofensivo, tudo bem —
      mas explicar qual.
- [ ] Zero 404 na aba de rede (fonte, ícone, imagem, JSON).

## Mobile e responsivo

- [ ] Testado em **390px de largura**, não só no monitor.
- [ ] Sem scroll horizontal.
- [ ] Alvo de toque com pelo menos ~44×44px.
- [ ] Texto legível sem zoom (mínimo 16px no corpo).
- [ ] Nada essencial escondido atrás de `:hover` — no celular não existe hover.

## Visual

Os números desta seção são o padrão: a direção escolhida pode trocar algum
deles dizendo por escrito por quê. Contraste, fundos alternados e
`prefers-reduced-motion` não entram nessa troca.

- [ ] **Fundos alternando por tom** (regra da pasta): dois blocos visíveis
      seguidos nunca claro/claro nem escuro/escuro, rodapé incluso —
      **medido** pela luminância computada, não olhado.
- [ ] Espaçamento vem de uma escala (4/8/12/16/24/32/48), não de números aleatórios.
- [ ] Máximo 2 famílias de fonte, e elas carregam de fato (checar rede).
- [ ] Contraste de texto normal ≥ 4.5:1 sobre o fundo.
- [ ] Hierarquia clara: dá para saber o que é título, o que é corpo, o que é ação
      principal, olhando 2 segundos.
- [ ] Se tem animação, ela tem propósito e é curta (150–400ms). Animação longa
      em coisa que se repete vira irritação.
- [ ] `prefers-reduced-motion` respeitado quando há movimento pesado.

## Acessibilidade mínima

- [ ] Dá para navegar e acionar o principal só pelo teclado (Tab, Enter, Esc).
- [ ] O foco do teclado é visível.
- [ ] Imagem que carrega informação tem `alt`; imagem decorativa tem `alt=""`.
- [ ] Modal fecha no Esc e devolve o foco de onde veio.

## Antes de fechar

- [ ] Nada de `console.log` de depuração sobrando.
- [ ] Nenhuma chave de API dentro de arquivo do front.
- [ ] Se editei algo que já funcionava, o que funcionava continua funcionando.
- [ ] Se eu não consegui verificar um item (sem navegador, sem dados, sem chave),
      **dizer que não verifiquei** em vez de marcar como feito.

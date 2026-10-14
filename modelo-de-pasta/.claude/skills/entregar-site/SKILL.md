---
name: entregar-site
description: Checklist de entrega antes de publicar um site de cliente ou colocar qualquer coisa no ar. Usar quando o usuário falar em publicar, subir, entregar, "está pronto pro cliente", fazer deploy na Cloudflare, ou mexer em algo que já está em produção.
argument-hint: "[projeto]"
disable-model-invocation: true
---

# Entrega de site

Isto aqui toca dinheiro e reputação. Um bug num projeto pessoal é chateação;
um formulário de contato quebrado num site de cliente é cliente perdido sem
ninguém nunca descobrir por quê.

Projeto: `$0`

## 0. Antes de tudo: é produção?

Conferir no mapa dos projetos (seção 8 das regras da raiz) se este projeto está marcado como de
**cliente** ou como **já no ar**. Se estiver, qualquer alteração aqui é
alteração em produção:

- **Confirmar com o usuário antes de mexer.** Não é pergunta retórica, é trava.
- Se o projeto tem `COMO-PUBLICAR.md` ou `README.md`, **ler antes** — o processo
  de publicação daquele site manda mais que esta skill.
- Nunca tocar em pasta `_originais/` — é material bruto insubstituível de
  cliente, e não tem cópia aqui.
- Nunca remover pasta que a seção 7 marcou como demo viva ou dependência de
  outro projeto, mesmo que pareça duplicata.

Se as regras da raiz não disserem nada sobre este projeto, **perguntar se é de
cliente** antes de continuar. Descobrir isso depois de publicar não adianta.

## 1. Rodar e olhar

Subir pelo `.claude/launch.json` e passar a `revisar-visual` inteira: screenshot
em 1440 e em 390, console limpo, zero 404 na rede. Ela também é manual — abrir
`.claude/skills/revisar-visual/SKILL.md` e seguir. Depois a `checklist-web`.

Se o app do agente tiver preview de projeto (o Claude Code Desktop tem, pelo
`launch.json`), o servidor já sobe por lá — usar isso em vez de subir na mão.

## 2. O que só importa na entrega

Coisas que não aparecem enquanto se desenvolve e aparecem para o cliente:

**Links e navegação**
- [ ] Todo link interno leva a uma página que existe. Nenhum `href="#"` sobrando.
- [ ] Menu funciona em todas as páginas, não só na home.
- [ ] Link externo abre em nova aba (`target="_blank"` com `rel="noopener"`).
- [ ] `404.html` existe e tem caminho de volta pra home.

**O que aparece quando compartilham no WhatsApp**
- [ ] `<title>` específico por página — não "Documento" nem o nome repetido em todas.
- [ ] `<meta name="description">` em cada página.
- [ ] Open Graph: `og:title`, `og:description`, `og:image` (imagem de pelo menos
      1200×630, com URL **absoluta**, não relativa — com relativa o preview quebra).
- [ ] Testar o preview de verdade, não confiar em ter escrito a tag.

**Identidade**
- [ ] Favicon existe e não é o padrão do navegador.
- [ ] Nome, telefone, e-mail, CNPJ e endereço **conferidos com o material do
      cliente**, caractere por caractere. Telefone errado é o pior erro possível aqui.
- [ ] Link de WhatsApp no formato `https://wa.me/55DDDNUMERO` e testado.
- [ ] Nenhum texto placeholder sobrando: "Lorem ipsum", "Seu texto aqui",
      "empresa@exemplo.com", "(00) 00000-0000".

**Formulário de contato** — se existir
- [ ] Enviar um de teste de verdade e **confirmar que chegou**. Formulário que
      não envia é o defeito mais caro e mais silencioso de site de PME.
- [ ] Campo obrigatório valida, e-mail inválido é recusado.
- [ ] Tem mensagem de sucesso e mensagem de erro.

**Peso e busca**
- [ ] Nenhuma imagem gigante servida direto do celular do cliente (4 MB de JPEG
      num banner). Redimensionar e comprimir — **cópia nova, nunca por cima do original**.
- [ ] `robots.txt` e `sitemap.xml` existem e apontam pro domínio certo.
- [ ] Rodar Lighthouse pela ferramenta de navegador do agente e reportar os números.
      Não perseguir 100; reportar o que estiver vermelho.

**Higiene**
- [ ] Zero `console.log` de depuração.
- [ ] Nenhuma chave de API no front.
- [ ] Nenhum comentário interno visível no HTML ("arrumar isso depois",
      "cliente não pagou ainda").

## 3. Publicar

- Seguir o `COMO-PUBLICAR.md` do projeto. Se não existir, perguntar como aquele
  site é publicado — **não inventar um processo de deploy.**
- **Publicar é decisão do usuário** (seção 7 das regras da raiz): mostrar o
  comando e esperar, a não ser que ele tenha liberado por escrito aquele
  projeto. Projeto de cliente **nunca** sobe sem ordem dele na conversa.
- Depois de publicar, **abrir a URL de produção** e conferir: página carrega,
  favicon aparece, um link interno funciona, preview de compartilhamento certo.
  Deploy que "deu certo" no terminal e 404 no ar acontece o tempo todo.

## 4. Relatar

```
No ar: <URL>
Conferido em produção: <o que eu realmente abri e testei>
Corrigido antes de subir: <lista>
Ficou pendente: <o que não deu, e por quê>
Precisa do cliente: <informação que faltou e só ele tem>
```

Se algum item não pôde ser verificado, dizer que não foi verificado. Não marcar
como feito o que não foi testado.

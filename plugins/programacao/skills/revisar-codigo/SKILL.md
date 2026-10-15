---
name: revisar-codigo
description: Use para revisar código (o seu, o de outra pessoa ou o que o Claude acabou de escrever) e achar erros, riscos e confusões antes que virem problema.
---

# Revisar código

Leia o código que mudou e o que está em volta dele. Procure, nesta ordem:

1. **Faz o que devia?** Compare com o pedido. Falta algum caso?
2. **Erros:** algo que quebra com entrada inesperada (vazio, nulo, acento, número grande), conta errada, condição invertida, arquivo que não fecha.
3. **Dados:** algo que pode apagar ou sobrescrever dado sem querer.
4. **Segurança:** senha, chave ou token no código; comando montado com texto de quem usa; caminho que pode sair da pasta.
5. **Clareza:** nome que engana, função gigante, comentário que mente.

Regras:
- Cada achado com arquivo, linha, o problema e uma sugestão concreta.
- Do mais grave para o menos grave. Não encha a lista com gosto pessoal.
- Se estiver bom, diga que está bom.
- Não mude nada sem a pessoa pedir.

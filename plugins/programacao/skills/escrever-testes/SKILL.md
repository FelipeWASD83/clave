---
name: escrever-testes
description: Use para criar testes automáticos que conferem se o código faz o que deve, inclusive nos casos difíceis, usando a ferramenta de testes que o projeto já usa.
---

# Escrever testes

1. Descubra como o projeto já testa (pasta `tests/` ou `testes/`, `pytest`, `unittest`, `node --test`, `npm test`). Use o mesmo jeito; não traga outra ferramenta sem motivo.
2. Teste o **comportamento**, não o jeito de fazer: entrada e saída esperada.
3. Para cada função importante, cubra:
   - o caso normal;
   - os limites (lista vazia, zero, texto com acento, número negativo, arquivo que não existe);
   - o erro esperado (o que deve acontecer quando a entrada é inválida).
4. Nome de teste que diz o que confere (`test_total_ignora_linhas_vazias`).
5. Rode os testes e mostre o resultado. Teste que falha porque o código tem um erro: **conte**, não mude o teste para passar.
6. Testes não podem mexer em dados reais: use pasta temporária e arquivos de exemplo.

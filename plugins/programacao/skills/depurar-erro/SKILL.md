---
name: depurar-erro
description: Use quando algo dá erro ou não funciona como deveria. Acha a causa de verdade antes de mudar o código, corrige com a menor mudança possível e confere.
---

# Depurar um erro

1. **Leia o erro inteiro**, de baixo para cima: a última linha diz o tipo, as de cima dizem onde. Peça a mensagem completa se a pessoa só disse "deu erro".
2. **Reproduza:** rode o mesmo comando ou faça o mesmo passo e veja o erro acontecer. Sem reproduzir, você está chutando.
3. **Hipótese:** escreva em uma frase o que você acha que causa o erro e por quê. Confirme lendo o código e, se precisar, imprimindo valores.
4. **Corrija a causa, não o sintoma:** a menor mudança que resolve. Não reescreva o resto, não "melhore" o que não tem a ver.
5. **Confira:** rode de novo o mesmo passo e mostre que o erro sumiu. Rode os testes, se houver.
6. **Explique em linguagem simples:** o que causava o erro, o que você mudou e se pode voltar a acontecer.

Se depois de duas tentativas a causa continuar escondida, pare e conte o que já descartou, em vez de sair mudando coisas.

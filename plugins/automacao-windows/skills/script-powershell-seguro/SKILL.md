---
name: script-powershell-seguro
description: Use ao criar um script de PowerShell que a pessoa vai rodar de novo (organizar, renomear, copiar, gerar relatório). O script mostra antes o que faria, guarda um registro e nunca apaga direto.
---

# Script de PowerShell seguro

## Regras do script
- **Ensaio por padrão:** o script começa com `param([switch]$Valendo)`. Sem `-Valendo`, ele só mostra o que faria. Explique isso para a pessoa.
- **Nada de apagar:** em vez de `Remove-Item`, mova para uma pasta `_lixeira` ao lado, com data no nome. Quem decide esvaziar é a pessoa.
- **Registro:** cada ação vai para um arquivo `registro-AAAA-MM-DD.csv` (data, ação, origem, destino). Com ele dá para desfazer.
- **Acentos:** salve o `.ps1` em UTF-8 **com BOM** (o PowerShell 5.1 do Windows lê sem BOM como outra codificação e estraga os acentos). Se o `escrever_arquivo` gravar sem BOM, avise e ofereça um `.bat` que chama o script.
- **Caminhos com espaço** sempre entre aspas; use `Join-Path` em vez de juntar texto.
- Erro para o script: `$ErrorActionPreference = 'Stop'` e `try/catch` com mensagem clara em português.
- Nunca use `Set-ExecutionPolicy` para o computador inteiro.

## Como entregar
1. Mostre o script e explique em 3 a 5 linhas o que ele faz.
2. Rode em modo ensaio e mostre o resultado.
3. Só rode com `-Valendo` depois do OK da pessoa.
4. Ensine a rodar de novo com dois cliques: crie um `.bat` ao lado:

```bat
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0meu-script.ps1" -Valendo
pause
```

5. Se for para rodar sozinho todo dia, ofereça a skill `automacao-windows:agendar-tarefa` ou uma Rotina do Clave.

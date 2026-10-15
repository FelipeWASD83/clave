---
name: limpar-dados
description: Use para arrumar uma planilha ou CSV bagunçado: espaços sobrando, linhas repetidas, datas e números em formatos misturados, acentos quebrados. Salva o resultado num arquivo novo e conta o que mudou.
---

# Limpar dados

## Antes
1. Abra o arquivo e descreva o problema com exemplos reais (ex.: "a coluna Data tem 12/03/2026 e 2026-03-12").
2. CSV brasileiro costuma usar `;` como separador e vírgula decimal. Acento quebrado (`SÃ£o Paulo`) é arquivo UTF-8 lido como Latin-1 (ou o contrário): descubra a codificação certa antes de mexer.
3. Combine com a pessoa o que fazer com o que é duvidoso (ex.: linha sem nome: apagar ou marcar?).

## Limpeza (nesta ordem)
1. Tirar espaços no começo e no fim; padronizar maiúsculas onde fizer sentido (nomes, siglas de estado).
2. Datas no formato dd/mm/aaaa (ou data de verdade, no Excel).
3. Números: tirar `R$`, ponto de milhar e trocar vírgula decimal pelo formato numérico.
4. Linhas repetidas: só remova as **idênticas**; as parecidas, liste para a pessoa decidir.
5. Células vazias: não invente valor; marque ou deixe vazio.

## Depois
- Salve num arquivo novo (ex.: `clientes - limpo.xlsx`) e mantenha a original intacta.
- Mostre um resumo: quantas linhas antes e depois, o que foi corrigido em cada coluna, o que ficou para decidir.
- Se a pessoa vai repetir isso todo mês, ofereça transformar a limpeza num script que ela roda de novo.

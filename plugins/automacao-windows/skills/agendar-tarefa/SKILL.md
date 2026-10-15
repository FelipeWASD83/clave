---
name: agendar-tarefa
description: Use quando a pessoa quiser que um script ou programa rode sozinho num horário (todo dia, toda semana, ao ligar o PC), pelo Agendador de Tarefas do Windows.
---

# Agendar uma tarefa no Windows

Primeiro pergunte: é um **script** (ou programa) ou um **pedido para o Claude**? Pedido para o Claude (ex.: "todo dia às 8h resuma meus e-mails da pasta X") cabe melhor numa **Rotina do Clave** (barra da esquerda > Rotinas), que já tem teto de gasto e regras de permissão.

## Para um script
1. Confirme que o script funciona rodando na mão primeiro.
2. Mostre o comando antes de rodar e explique cada parte. Use uma pasta própria no Agendador, para a pessoa achar depois:

```powershell
$acao = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"C:\caminho\meu-script.ps1`" -Valendo"
$quando = New-ScheduledTaskTrigger -Daily -At 18:00
Register-ScheduledTask -TaskPath "\Minhas automações\" -TaskName "Organizar Downloads" -Action $acao -Trigger $quando -Description "Criada com o Clave"
```

   Outros gatilhos: `-Weekly -DaysOfWeek Monday,Friday -At 9:00`, `-AtLogOn`.
3. Teste na hora: `Start-ScheduledTask -TaskPath "\Minhas automações\" -TaskName "Organizar Downloads"` e confira o resultado (o registro do script).
4. Ensine a desligar e a apagar:
   - pelo app **Agendador de Tarefas** (menu Iniciar), pasta "Minhas automações";
   - ou `Disable-ScheduledTask` / `Unregister-ScheduledTask` com os mesmos nomes (apagar pede o OK da pessoa no Clave).

## Cuidados
- A tarefa roda com o usuário de quem criou e só com o PC ligado.
- Nada que precise de administrador sem a pessoa entender o porquê.
- Script agendado tem que ter registro (log): é o único jeito de saber o que ele fez sozinho.

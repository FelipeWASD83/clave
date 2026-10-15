---
name: depurar-erro
description: Use when something fails or doesn't work as it should. Finds the real cause before changing the code, fixes it with the smallest possible change and checks the result.
---

# Debug an error

1. **Read the whole error**, from the bottom up: the last line says the type, the ones above say where. Ask for the full message if the person only said "it gave an error".
2. **Reproduce it:** run the same command or do the same step and watch the error happen. If you can't reproduce it, you are guessing.
3. **Hypothesis:** write in one sentence what you think causes the error and why. Confirm it by reading the code and, if needed, printing values.
4. **Fix the cause, not the symptom:** the smallest change that solves it. Don't rewrite the rest, don't "improve" what is unrelated.
5. **Check:** run the same step again and show that the error is gone. Run the tests, if there are any.
6. **Explain in plain language:** what caused the error, what you changed and whether it can happen again.

If after two attempts the cause is still hidden, stop and say what you have already ruled out, instead of changing things at random.

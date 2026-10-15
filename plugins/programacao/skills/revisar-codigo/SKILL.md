---
name: revisar-codigo
description: Use to review code (your own, someone else's or what Claude just wrote) and find errors, risks and confusion before they turn into problems.
---

# Review code

Read the code that changed and what surrounds it. Look for, in this order:

1. **Does it do what it should?** Compare it with the request. Is any case missing?
2. **Errors:** anything that breaks with unexpected input (empty, null, accents, large numbers), a wrong calculation, an inverted condition, a file that never gets closed.
3. **Data:** anything that could delete or overwrite data by accident.
4. **Security:** a password, key or token in the code; a command built from the user's text; a path that can escape the folder.
5. **Clarity:** a misleading name, a giant function, a comment that lies.

Rules:
- Each finding with file, line, the problem and a concrete suggestion.
- From most to least serious. Don't pad the list with personal taste.
- If it is good, say it is good.
- Don't change anything unless the person asks.

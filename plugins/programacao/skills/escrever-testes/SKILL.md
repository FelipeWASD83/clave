---
name: escrever-testes
description: Use to create automated tests that check whether the code does what it should, including the hard cases, using the testing tool the project already uses.
---

# Write tests

1. Find out how the project already tests (a `tests/` or `testes/` folder, `pytest`, `unittest`, `node --test`, `npm test`). Use the same way; don't bring in another tool without a reason.
2. Test the **behavior**, not how it is done: input and expected output.
3. For each important function, cover:
   - the normal case;
   - the limits (empty list, zero, text with accents, negative number, a file that doesn't exist);
   - the expected error (what should happen when the input is invalid).
4. Give each test a name that says what it checks (`test_total_ignora_linhas_vazias`).
5. Run the tests and show the result. If a test fails because the code has a bug: **say so**, don't change the test to make it pass.
6. Tests must not touch real data: use a temporary folder and sample files.

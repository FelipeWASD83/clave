# GML pitfalls

Mistakes I make by reflex, each one checked against the official manual on
2026-09-02 (`monthly` channel). Where the source matters, the page path is at
the end of the item: you can reread it with `python docgml.py ver <path>`.

This is not a summary of the language. It is the list of what I get wrong.

---

## 1. Functions that no longer exist (but I write them by reflex)

| What I write | What exists today |
|---|---|
| `instance_create(x, y, obj)` | `instance_create_layer(x, y, layer, obj)` or `instance_create_depth(x, y, depth, obj)` |
| `array_length_1d(a)` / `array_length_2d(a)` | `array_length(a)`: the old ones exist but the manual marks them DEPRECATED, and `array_length_1d` gets it wrong above 32,000 entries |
| `d3d_*` | nothing: the whole family is gone from the manual |
| `argument0`, `argument1` in a script | named functions with parameters: `function name(_a, _b)` |

The pattern here is always the same: **GMS 1.x content still dominates the
internet**. When a snippet "looks like" GameMaker but doesn't match the manual,
it is almost always code from 2015.

## 2. Arrays are passed by reference: copy-on-write is over

Today, modifying an array inside a function **modifies the original array**.
The old *Copy on Write* is marked as deprecated in the manual and only comes
back if the option "Enable Copy on Write behaviour for Arrays" is turned on in
General Game Options.

Practical consequence: **stop writing `array[@ i] = v` by reflex**. With CoW
off (the default), `array[i] = v` inside a function already changes the
original. The `@` is only needed if the project has the legacy option turned
on, which you find out by looking at the project options, not by guessing.

Careful: the manual's own `Data_Types.htm` page still describes the old
behavior ("will then become a copy of the original array"). **Two pages of the
manual contradict each other.** When that happens, the page specific to the
subject (`GML_Overview/Arrays.htm`) and the release notes win over the generic page.

`GameMaker_Language/GML_Overview/Arrays.htm`

## 3. A function's return value can't be on the left of an assignment

```gml
instance_nearest(x, y, obj).speed = 0;      // compile error
(instance_nearest(x, y, obj)).speed = 0;    // works
var _inst = instance_nearest(x, y, obj);    // better
_inst.speed = 0;
```

`GameMaker_Language/GML_Overview/Runtime_Functions.htm`

## 4. Chained assignment doesn't exist

`a = b = c = 4;` doesn't do what it looks like. Write one line per variable.
(And `:=` is accepted as a synonym for `=`, but nobody uses it: don't introduce it.)

## 5. `#RRGGBB` and `$RRGGBB` are not the same number

GML reads color as BGR. `$2c8edd` is **not** `#2c8edd`; the equivalent is
`#dd8e2c`. The `#` prefix exists precisely to accept color in the CSS format.
Getting this wrong produces a game with swapped colors and no compile error.

Hexadecimal accepts `$abcd` and `0xabcd`; binary accepts `0b0110`.

`GameMaker_Language/GML_Overview/Data_Types.htm`

## 6. British spelling

The manual documents **only** `colour`: none of the 3113 pages uses `color`.
Both spellings compile, but this skill's index only knows the British one
(`checar-gml.py` handles the conversion). **Write in the manual's spelling**
and, inside an existing project, follow the spelling the project already uses.

## 7. A boolean is a real in disguise

Any real **greater than 0.5** is `true`; `<= 0.5` is `false`. Always use the
constants `true`/`false` and never compare with `1`/`0`.

`GameMaker_Language/GML_Overview/Data_Types.htm`

## 8. An invalid handle is not `undefined`

- Invalid instance: `noone` (which equals `-4`), **not** `-1`, **not** `undefined`.
- Any other handle (list, buffer, surface, sprite...): `-1`.
- Indexes are **recycled**: destroying one list and creating another can return
  the same number. After destroying, reset the variable (`-1` or `noone`),
  otherwise it ends up pointing to a new resource that belongs to someone else.

`GameMaker_Language/GML_Overview/Data_Types.htm`

## 9. Structs: the right side of the `:` can't see the struct

```gml
mystruct = { a : 10, b : 10, c : a + b };   // error: a and b are looked up outside
```

Everything to the right of the colon is evaluated **in the scope of whoever is
creating the struct** (the instance, for example). That is why `{ x : x, y : y }`
works and copies the instance's `x`/`y`, and why the shortcut `{ a, b, c: 101 }`
exists for variables of the same name.

Structs and arrays are **collected by the garbage collector**. `delete` only
prioritizes the collection, it isn't mandatory.

`GameMaker_Language/GML_Overview/Structs.htm`

## 10. DS* are not collected; structs and arrays are

`ds_list`, `ds_map`, `ds_grid`, `ds_stack`, `ds_queue` and `ds_priority`
**need a manual `*_destroy()`**, otherwise they leak memory. The manual itself
recommends preferring arrays and structs, which are collected on their own.

Don't go converting `ds_*` in an existing project to structs because of this:
see the attitude rule in `SKILL.md`.

`GameMaker_Language/GML_Reference/Data_Structures/Data_Structures.htm`

## 11. Accessors: each structure has its own symbol

| Structure | Syntax |
|---|---|
| DS List | `list[| index]` |
| DS Map | `map[? key]` |
| DS Grid | `grid[# x, y]` |
| Struct | `st[$ "name"]` |
| Array (direct write, legacy CoW) | `arr[@ i]` |

Out of range, list/map/grid return `undefined` (check with `is_undefined`),
they don't raise an error.

`GameMaker_Language/GML_Overview/Accessors.htm`

## 12. Variable names

They start with a letter or `_`, only alphanumeric characters and `_`, **at
most 64 characters**. They can't repeat the name of an asset in the project
(unless qualified with `self.`/`global.`). Reserved and forbidden:
`player_avatar_sprite`, `player_avatar_url`, `player_id`, `player_local`,
`player_name`, `player_type`, `player_user_id`, `player_prefs`, `managed`.

There is also a list of forbidden names inside structs:
`GameMaker_Language/GML_Overview/Struct_Forbidden_Variables.htm`

## 13. Template strings exist: use them

```gml
show_debug_message($"health: {hp}/{hp_max}");
```

Introduced in recent versions (it is in LTS 2026.0). In an old project, check
the version before using it; if it is old, fall back to `string()` and
concatenation.

## 14. Scope rules that I mix up

- Without `var`, inside an event, the variable is an **instance** variable and
  survives the event. With `var`, it is **local** and dies at the end of the
  event/function.
- `other` inside `with` is whoever called the `with`, not a generic "other".
- `self` inside a struct is the struct, not the instance that created it.

`GameMaker_Language/GML_Overview/Variables_And_Variable_Scope.htm`

# PA 7: The Parameter Simulator

Monica Monterrosa  
CS 379: Programming Languages  
Part A: The Specification

## 1. Three Modes, One Function

The caller starts with `x = 1` and `y = 2` and calls:

```text
swap(a, b) {
    let t = a;
    a = b;
    b = t;
}
swap(x, y);
```

In each trace, the callee's activation record has `function_name = "swap"`,
`return_address = "call site"`, and the parameter bindings in `locals_env`.
The harness uses `None` for both frame links in this simulation. A cell is a
mutable storage slot; the numbers shown in the tables are its current contents.
The local variable `t` always has its own callee cell.

### Pass-by-value

Binding creates two new cells in the callee: `a = Cell(1)` and `b = Cell(2)`.
They are distinct from the caller's cells for `x` and `y`.

| Step | Callee a | Callee b | Callee t | Caller x | Caller y |
| --- | ---: | ---: | ---: | ---: | ---: |
| Bind arguments | 1 | 2 | Not declared | 1 | 2 |
| `let t = a` | 1 | 2 | 1 | 1 | 2 |
| `a = b` | 2 | 2 | 1 | 1 | 2 |
| `b = t` | 2 | 1 | 1 | 1 | 2 |
| Return | 2 | 1 | 1 | 1 | 2 |

The callee owns the writable parameter cells. Assigning to its parameter names
does not update the caller's variable cells, and there is no copy-back at return.
The final caller values are **x = 1, y = 2**. The callee cells disappear when the
frame is no longer needed; the return row shows their final contents.

### Pass-by-reference

Binding makes `a` refer to the exact cell used by caller `x`, and `b` refer to
the exact cell used by caller `y`. No separate parameter cells are allocated.

| Step | Callee a (aliases x) | Callee b (aliases y) | Callee t | Caller x | Caller y |
| --- | ---: | ---: | ---: | ---: | ---: |
| Bind arguments | 1 | 2 | Not declared | 1 | 2 |
| `let t = a` | 1 | 2 | 1 | 1 | 2 |
| `a = b` | 2 | 2 | 1 | 2 | 2 |
| `b = t` | 2 | 1 | 1 | 2 | 1 |
| Return | 2 | 1 | 1 | 2 | 1 |

The caller owns the cells, and the callee shares them. Each assignment is visible
to the caller immediately, even before return. The final caller values are
**x = 2, y = 1**.

### Pass-by-value-result

Binding creates private callee cells `a = Cell(1)` and `b = Cell(2)` and records
the caller's destination cells in parameter order: `a -> x`, then `b -> y`.

| Step | Callee a | Callee b | Callee t | Caller x | Caller y |
| --- | ---: | ---: | ---: | ---: | ---: |
| Copy in | 1 | 2 | Not declared | 1 | 2 |
| `let t = a` | 1 | 2 | 1 | 1 | 2 |
| `a = b` | 2 | 2 | 1 | 1 | 2 |
| `b = t` | 2 | 1 | 1 | 1 | 2 |
| Return: copy a to x | 2 | 1 | 1 | 2 | 2 |
| Return: copy b to y | 2 | 1 | 1 | 2 | 1 |

The callee owns its writable parameter cells during execution. The caller owns
the destination cells. Parameter assignments become visible in those destinations
only during copy-back at return. The final caller values are **x = 2, y = 1**.

### Tests that distinguish the modes

| Mode | Writable cell relationship | Test exposing an incorrect implementation |
| --- | --- | --- |
| Value | Callee has a new cell | Verify different cell identities; assign 15 to the parameter and verify caller a stays 10. |
| Reference | Callee shares caller's cell | Verify identical cell identities; assign 12 and check caller a is 12 before return. |
| Value-result | Callee has a new cell plus a saved caller destination | Assign 20; verify caller a remains 12 before commit and becomes 20 after commit. |

The three `swap` checks confirm the final results. However, reference and
value-result both swap distinct caller variables successfully, so the
return-time visibility checks are necessary to distinguish their timing.

Copying a value into a new cell does not deep-copy a mutable Python object.
For example, two distinct cells can contain the same list object. Mutating that
list may be visible through either cell, but assigning a different value to the
callee's parameter name still changes only its private cell in value mode.
Object sharing is separate from sharing a variable's writable cell.

## 2. Asymmetric Aliasing

The caller starts with `a = 10` and invokes:

```text
P(x, y) {
    x = x + 1;
    y = y + 1;
}
P(a, a);
```

### Pass-by-reference

Both parameters refer to the same caller cell: `x -> a` and `y -> a`.

| Step | Callee x | Callee y | Caller a |
| --- | ---: | ---: | ---: |
| Bind arguments | 10 | 10 | 10 |
| `x = x + 1` | 11 | 11 | 11 |
| `y = y + 1` | 12 | 12 | 12 |
| Return | 12 | 12 | 12 |

The first assignment changes the shared cell to 11. The second assignment reads
11 through `y` and writes 12 into that same cell. The caller immediately observes
each write. The final caller value is **a = 12**.

### Pass-by-value-result

The callee gets two distinct cells, initially `x = Cell(10)` and `y = Cell(10)`.
Both saved copy-back destinations point to the caller's same `a` cell.

| Step | Callee x | Callee y | Caller a |
| --- | ---: | ---: | ---: |
| Copy in | 10 | 10 | 10 |
| `x = x + 1` | 11 | 10 | 10 |
| `y = y + 1` | 11 | 11 | 10 |
| Return: copy x to a | 11 | 11 | 11 |
| Return: copy y to a | 11 | 11 | 11 |

Each assignment reads its own local cell, so both locals independently become
11. At return, copying `x` writes 11 to `a`; copying `y` then writes 11 to the
same destination. The final caller value is **a = 11**. Unlike reference mode,
the second increment never sees the first parameter's updated local value.

The asymmetric `P(a,a)` checks expose an implementation that incorrectly treats
value-result as reference. A symmetric `swap(a,a)` leaves the value unchanged
under either mode and cannot establish this difference. In this particular
increment example both final local values are 11, so reversing copy-back would
give the same numeric result. To expose reversed order directly, give the two
value-result locals different final values, such as x = 20 and y = 30; with
both targeting a, the required x-then-y copy-back must leave a = 30.

## 3. Closures and Capture

All three closures return **3**, producing `[3, 3, 3]` when called after the loop.
They retain the defining environment containing the same mutable cell for `i`.
They do not save independent snapshots of 0, 1, and 2. The final increment makes
that shared cell contain 3, and the failed `i < 3` condition ends the loop.

In PA 6, a static link represents a function's lexical enclosing context.
Here, `Closure` stores `defining_env`. Each call creates a fresh environment
whose parent is that saved environment; this parent link performs the lexical
lookup role of the static link. Looking up the free name `i` follows the parent
link to the same cell for every closure. The identity of the calling environment
does not change this lexical lookup. The closure keeps its defining environment
reachable even after the code that created it has finished.

To make the closures return `[0, 1, 2]`, change the `for` semantics to allocate a
fresh iteration environment and a distinct cell for `i` on each iteration.
The body runs in that iteration's environment, so each closure naturally captures
a different cell using the unchanged closure mechanism. After the body, copy the
loop binding into a fresh environment for the update and next condition; increment
that fresh binding, leaving the cell captured by the completed iteration unchanged.
The cells retained by the three body closures therefore remain 0, 1, and 2.
Merely allocating new environment objects that all share the old `i` cell would
still produce shared capture and would not fix the result.

The harness checks shared capture by expecting `[3, 3, 3]`. It also defines
`captured = 100` in the defining environment and `captured = 999` in an unrelated
caller: the closure must return 100. Calls with an `offset` parameter must get
fresh parameter cells and return 105 and 107 for arguments 5 and 7.

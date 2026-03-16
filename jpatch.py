#!/usr/bin/env python3
"""jsonpatch - Apply RFC 6902 JSON Patch operations on JSON files. Zero deps."""
import json, sys, copy, re

def resolve_pointer(doc, pointer):
    """Resolve JSON Pointer (RFC 6901). Returns (parent, key)."""
    if pointer == "": return None, None
    parts = pointer.lstrip("/").split("/")
    parts = [p.replace("~1","/").replace("~0","~") for p in parts]
    cur = doc
    for i, p in enumerate(parts[:-1]):
        if isinstance(cur, list):
            cur = cur[int(p)]
        else:
            cur = cur[p]
    last = parts[-1]
    if isinstance(cur, list):
        last = len(cur) if last == "-" else int(last)
    return cur, last

def get_value(doc, pointer):
    if pointer == "": return doc
    parent, key = resolve_pointer(doc, pointer)
    if isinstance(parent, list): return parent[key]
    return parent[key]

def op_add(doc, path, value, **_):
    if path == "": return value
    parent, key = resolve_pointer(doc, path)
    if isinstance(parent, list):
        parent.insert(key, value)
    else:
        parent[key] = value
    return doc

def op_remove(doc, path, **_):
    parent, key = resolve_pointer(doc, path)
    if isinstance(parent, list): parent.pop(key)
    else: del parent[key]
    return doc

def op_replace(doc, path, value, **_):
    parent, key = resolve_pointer(doc, path)
    if isinstance(parent, list): parent[key] = value
    else: parent[key] = value
    return doc

def op_move(doc, path, **kw):
    frm = kw["from"]
    val = get_value(doc, frm)
    doc = op_remove(doc, frm)
    return op_add(doc, path, val)

def op_copy(doc, path, **kw):
    frm = kw["from"]
    val = copy.deepcopy(get_value(doc, frm))
    return op_add(doc, path, val)

def op_test(doc, path, value, **_):
    actual = get_value(doc, path)
    if actual != value:
        raise ValueError(f"Test failed: {path} = {json.dumps(actual)}, expected {json.dumps(value)}")
    return doc

OPS = {"add": op_add, "remove": op_remove, "replace": op_replace,
       "move": op_move, "copy": op_copy, "test": op_test}

def apply_patch(doc, patch):
    for i, op in enumerate(patch):
        fn = OPS.get(op["op"])
        if not fn: raise ValueError(f"Unknown op: {op['op']}")
        doc = fn(doc, **{k:v for k,v in op.items() if k != "op"})
    return doc

def cmd_apply(args):
    if len(args) < 2:
        print("Usage: jsonpatch apply <file.json> <patch.json> [--in-place]")
        sys.exit(1)
    with open(args[0]) as f: doc = json.load(f)
    with open(args[1]) as f: patch = json.load(f)
    result = apply_patch(doc, patch)
    if "--in-place" in args:
        with open(args[0], "w") as f: json.dump(result, f, indent=2)
        print(f"Patched {args[0]} in place")
    else:
        print(json.dumps(result, indent=2))

def cmd_diff(args):
    """Generate a patch from two JSON files."""
    if len(args) < 2:
        print("Usage: jsonpatch diff <old.json> <new.json>")
        sys.exit(1)
    with open(args[0]) as f: old = json.load(f)
    with open(args[1]) as f: new = json.load(f)
    patch = generate_diff(old, new, "")
    print(json.dumps(patch, indent=2))

def generate_diff(old, new, path):
    ops = []
    if type(old) != type(new):
        return [{"op":"replace","path":path,"value":new}]
    if isinstance(old, dict):
        for k in set(list(old.keys()) + list(new.keys())):
            p = f"{path}/{k.replace('~','~0').replace('/','~1')}"
            if k not in new: ops.append({"op":"remove","path":p})
            elif k not in old: ops.append({"op":"add","path":p,"value":new[k]})
            else: ops.extend(generate_diff(old[k], new[k], p))
    elif isinstance(old, list):
        # Simple: if different, replace
        if old != new: ops.append({"op":"replace","path":path,"value":new})
    else:
        if old != new: ops.append({"op":"replace","path":path,"value":new})
    return ops

def cmd_get(args):
    if len(args) < 2:
        print("Usage: jsonpatch get <file.json> <pointer>")
        sys.exit(1)
    with open(args[0]) as f: doc = json.load(f)
    print(json.dumps(get_value(doc, args[1]), indent=2))

CMDS = {"apply": cmd_apply, "diff": cmd_diff, "get": cmd_get}

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] in ("-h","--help"):
        print("jsonpatch - RFC 6902 JSON Patch tool")
        print("Commands: apply, diff, get")
        print("  apply <file> <patch> [--in-place]")
        print("  diff <old> <new>  — generate patch")
        print("  get <file> <pointer>  — resolve JSON pointer")
        sys.exit(0)
    cmd = args[0]
    if cmd not in CMDS:
        print(f"Unknown: {cmd}"); sys.exit(1)
    CMDS[cmd](args[1:])

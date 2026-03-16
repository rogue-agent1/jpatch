# jpatch

RFC 6902 JSON Patch tool with diff generation. Zero dependencies.

## Commands

```bash
jpatch apply <file> <patch> [--in-place]   # Apply patch
jpatch diff <old> <new>                     # Generate patch
jpatch get <file> <pointer>                 # Resolve JSON Pointer
```

## Supported Operations

- `add`, `remove`, `replace`, `move`, `copy`, `test`

## Example

```bash
# Generate a patch between two files
python3 jpatch.py diff old.json new.json > patch.json

# Apply it
python3 jpatch.py apply old.json patch.json

# Query a value
python3 jpatch.py get config.json /database/host
```

## Requirements

- Python 3.6+ (stdlib only)

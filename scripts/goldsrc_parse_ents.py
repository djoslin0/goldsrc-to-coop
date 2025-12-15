import re
from goldsrc_parse_entities import *

def parse_entities_file(filepath):
    """Parse a GoldSrc-style entity lump file into a list of dicts, with simple logging."""
    print(f"Parsing entity file: {filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    except Exception as e:
        print(f"❌ Failed to read file: {e}")
        return []

    # Split the text into entity blocks {...}
    blocks = re.findall(r'\{([^}]*)\}', text, re.DOTALL)
    print(f"Found {len(blocks)} entity blocks")

    entities = []
    for _, block in enumerate(blocks, 1):
        entity = {}
        # Find all key-value pairs like "key" "value"
        pairs = re.findall(r'"([^"]+)"\s+"([^"]*)"', block)
        for key, value in pairs:
            entity[key] = value
        entities.append(entity)

    return entities

def interpret_entities(entities, bspguy_scalar, to_sm64_coords):
    iscalar = 1 / -bspguy_scalar
    if to_sm64_coords != 0:
        iscalar *= 100

    for ent in entities:
        parse_position(ent, 'origin', iscalar)
        classname = ent.get("classname", '?')
        if classname in parse_classes:
            for field in parse_classes[classname]:
                if field.startswith('_'):
                    continue
                parse_classes[classname][field](ent, field, iscalar)

def dump_entities_to_lua(entities):
    lines = []
    for ent in entities:
        lines.append("        {")
        for k, v in ent.items():
            # Always produce safe Lua key syntax
            lua_key = f'["{k}"]'

            # Format value
            if isinstance(v, str):
                lua_value = f'"{v}"'
                lua_value = lua_value.replace('\\', '/')
            elif isinstance(v, (int, float)):
                lua_value = str(v)
            elif isinstance(v, tuple):
                lua_value = "{" + ", ".join(str(x) for x in v) + "}"
            else:
                lua_value = str(v)

            lines.append(f"            {lua_key} = {lua_value},")
        lines.append("        },")
    return "\n".join(lines)

def convert_entities_to_lua(entities_filepath, bspguy_scalar):
    entities = parse_entities_file(entities_filepath)
    interpret_entities(entities, bspguy_scalar, 1)
    return entities, dump_entities_to_lua(entities)

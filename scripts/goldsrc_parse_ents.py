import os
import sys
import re

def parse_entities(filepath):
    """Parse a GoldSrc-style entity lump file into a list of dicts, with simple logging."""
    print(f"Parsing entity file: {filepath}")

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
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

###############################

def interpret_string(entity, field, iscalar):
    pass

def interpret_position(entity, field, iscalar):
    if entity == None or field == None or field not in entity:
        return
    x, y, z = map(float, entity[field].split())
    entity[field] = (x * iscalar, y * iscalar, z * iscalar)

def interpret_angles(entity, field, iscalar):
    if entity == None or field == None or field not in entity:
        return
    x, y, z = map(float, entity[field].split())
    entity[field] = (x, y, z)

def interpret_color(entity, field, iscalar):
    if entity == None or field == None or field not in entity:
        return
    x, y, z = map(int, entity[field].split())
    entity[field] = (x, y, z)

def interpret_int(entity, field, iscalar):
    if entity == None or field == None or field not in entity:
        return
    entity[field] = int(entity[field])

def interpret_float(entity, field, iscalar):
    if entity == None or field == None or field not in entity:
        return
    entity[field] = float(entity[field])

def interpret_float_scaled(entity, field, iscalar):
    if entity == None or field == None or field not in entity:
        return
    entity[field] = float(entity[field]) * iscalar

###############################

interpret_classes = {
    "func_door" : {
        "classname": interpret_string,
        "targetname": interpret_string,
        "model": interpret_string,
        "angles": interpret_angles,

        "speed": interpret_float_scaled,
        "wait": interpret_float,
        "lip": interpret_float_scaled,
        "delay": interpret_float,
        "health": interpret_int,

        "movesnd": interpret_int,
        "stopsnd": interpret_int,
        "locked_sound": interpret_int,
        "unlocked_sound": interpret_int,
        "locked_sentence": interpret_int,
        "unlocked_sentence": interpret_int,

        "renderamt": interpret_int,
        "rendercolor": interpret_color,
        "rendermode": interpret_int,
        "renderfx": interpret_int,

        "target": interpret_string,
        "killtarget": interpret_string,
        "spawnflags": interpret_int,

        "dmg": interpret_int,
    }
}

###############################

def interpret_entities(entities, bspguy_scalar, to_sm64_coords):
    iscalar = 1 / -bspguy_scalar
    if to_sm64_coords != 0:
        iscalar *= 100

    for ent in entities:
        interpret_position(ent, 'origin', iscalar)
        classname = ent.get("classname", '?')
        if classname in interpret_classes:
            for field in interpret_classes[classname]:
                interpret_classes[classname][field](ent, field, iscalar)

def print_entities(entities, classname=None):
    for i, ent in enumerate(entities, 1):
        if classname != None and ent.get("classname", '?') != classname:
            continue
        print(f"Entity {i}:")
        for k, v in ent.items():
            print(f"  {k}: {v}")
        print()

def dump_entities_to_lua(entities):
    """Convert the entities list to a valid Lua code string."""
    lines = []
    for ent in entities:
        lines.append("        {")
        for k, v in ent.items():
            lua_key = k.replace('#', '_')
            if isinstance(v, str):
                lua_value = f'"{v}"'
                lua_value = lua_value.replace('\\', '/')
            elif isinstance(v, (int, float)):
                lua_value = str(v)
            elif isinstance(v, tuple):
                lua_value = "{" + ", ".join(str(x) for x in v) + "}"
            else:
                lua_value = str(v)  # fallback
            lines.append(f"            {lua_key} = {lua_value},")
        lines.append("        },")
    return "\n".join(lines)

def convert_entities_to_lua(entities_filepath, bspguy_scalar):
    entities = parse_entities(entities_filepath)
    interpret_entities(entities, bspguy_scalar, 1)
    return dump_entities_to_lua(entities)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python goldsrc-parse-ents.py <filepath> <bspguy scalar> <to_sm64_coords>")
        sys.exit(1)
    filepath = sys.argv[1]
    bspguy_scalar = int(sys.argv[2])
    to_sm64_coords = int(sys.argv[3])
    entities = parse_entities(filepath)
    interpret_entities(entities, bspguy_scalar, to_sm64_coords)
    print_entities(entities, "func_door")
    lua_code = dump_entities_to_lua(entities)
    print("\n--- Lua dump ---")
    print(lua_code)

import os
import sys
import re
from goldsrc_parse_ents import convert_entities_to_lua

# Load the template from template-main.lua
script_dir = os.path.dirname(os.path.abspath(__file__))

lua_files = [
    'a-goldsrc-1.lua',
    'template-main.lua',
    'template-a-goldsrc-level.lua',
]

def collect_register_objects(output_dir):
    actors_dir = os.path.join(output_dir, "actors")
    if not os.path.isdir(actors_dir):
        return ''

    output = ''

    for folder in os.listdir(actors_dir):
        folder_path = os.path.join(actors_dir, folder)
        if not os.path.isdir(folder_path):
            continue

        # Match folders ending with _ent_NUMBER
        match = re.search(r'_ent_(\d+)$', folder)
        if not match:
            continue

        entity_index = int(match.group(1))
        geo = os.path.exists(os.path.join(folder_path, "geo.inc.c"))
        col = os.path.exists(os.path.join(folder_path, "collision.inc.c"))

        if geo:
            output += f'entities[{entity_index+1}]._geo = smlua_model_util_get_id("{folder}_geo")\n'

        if col:
            output += f'entities[{entity_index+1}]._col = smlua_collision_util_get("{folder}_collision")\n'

    return output

def get_aabbs(path):
    with open(path, 'r') as f:
        return f.read()

def main():
    if len(sys.argv) < 4:
        print("Usage: python generate_level_script.py <levelname> <entities.txt filepath> <bspguy_scale>")
        sys.exit(1)

    levelname = sys.argv[1]
    leveluname = levelname.upper()
    entities_path = sys.argv[2]
    bspguy_scale = int(sys.argv[3])

    # Build output path
    output_dir = os.path.join("output", levelname, "mod")

    # Create directories if needed
    os.makedirs(output_dir, exist_ok=True)

    # Parse entities
    entities, entities_lua = convert_entities_to_lua(entities_path, bspguy_scale)

    # Set template variables
    template_variables = {
        "$LEVELNAME":        levelname,
        "$LEVELUNAME":       leveluname,
        "$ENTITIES":         entities_lua,
        "$REGISTER_OBJECTS": collect_register_objects(output_dir),
        "$AABBS":            get_aabbs(os.path.join("output", levelname, "aabb.lua")),
    }

    # Figure out which classes to include
    for entity in entities:
        lua_filename = f"a-goldsrc-{entity['classname']}.lua"
        lua_local_path = os.path.join("classes", lua_filename)
        lua_path = os.path.join(script_dir, "lua", lua_local_path)
        if os.path.exists(lua_path) and lua_local_path not in lua_files:
            lua_files.append(lua_local_path)

    # Generate lua files
    for lua_file in lua_files:
        print('Reading lua file ' + os.path.join(script_dir, "lua", lua_file))
        # Read
        with open(os.path.join(script_dir, "lua", lua_file), 'r', encoding='utf-8') as f:
            lua_source = f.read()

        # Replace template variables
        for k, v in template_variables.items():
            lua_source = lua_source.replace(k, v)

        # Output lua file
        output_lua_filename = os.path.basename(lua_file.replace('template-', ''))
        print('Writing lua file ' + os.path.join(output_dir, output_lua_filename))
        with open(os.path.join(output_dir, output_lua_filename), 'w', encoding='utf-8') as f:
            f.write(lua_source)

    print(f"✅ Mod generated at: {output_dir}")

if __name__ == "__main__":
    main()

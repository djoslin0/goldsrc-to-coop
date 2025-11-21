import os
import sys
import re
import shutil
from goldsrc_parse_ents import convert_entities_to_lua

# Load the template from template-main.lua
script_dir = os.path.dirname(os.path.abspath(__file__))

template_files = [
    [ 'template-main.lua', 'main.lua'],
    [ 'template-level.lua', 'a-goldsrc-$LEVELNAME.lua'],
]

subclasses = {
    'trigger_once': [ 'trigger_multiple' ],
    'func_door_rotating': [ 'func_door' ],
    'cycler_sprite': [ 'cycler' ],
}

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

def process_textures(path, missing_png_path):
    levels_dir = os.path.join(path, 'levels')
    actors_dir = os.path.join(path, 'actors')
    textures_dir = os.path.join(path, 'textures')
    os.makedirs(textures_dir, exist_ok=True)

    png_files = []

    # Collect PNGs from levels (recursive)
    if os.path.exists(levels_dir):
        for root, dirs, files in os.walk(levels_dir):
            for file in files:
                if file.lower().endswith('.png'):
                    png_files.append(os.path.join(root, file))

    # Collect PNGs from actors (recursive)
    if os.path.exists(actors_dir):
        for root, dirs, files in os.walk(actors_dir):
            dirs[:] = [d for d in dirs if not d.endswith('_mdl')]
            for file in files:
                if file.lower().endswith('.png'):
                    png_files.append(os.path.join(root, file))

    # Process each PNG
    for png_path in png_files:
        # Copy to textures directory
        dest = os.path.join(textures_dir, os.path.basename(png_path))
        shutil.copy2(png_path, dest)

        # Replace original with copy of missing_png_path
        shutil.copy2(missing_png_path, png_path)

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

    # Copy goldsrc dir
    shutil.copytree(os.path.join(script_dir, "lua", "goldsrc"), os.path.join(output_dir, "goldsrc"), dirs_exist_ok=True)

    # Figure out used classnames
    class_exports = []
    for entity in entities:
        if entity['classname'] in class_exports:
            continue
        class_exports.append(entity['classname'])

    # Figure out dependencies
    for classname in class_exports:
        if classname not in subclasses:
            continue
        for dependency in subclasses[classname]:
            if dependency in class_exports:
                continue
            class_exports.append(dependency)

    # Copy classfiles over
    class_requires = []
    for classname in class_exports:
        lua_filename = f"{classname}.lua"
        lua_local_path = os.path.join("classes", lua_filename)
        lua_path_r = os.path.join(script_dir, "lua", lua_local_path)
        lua_path_w = os.path.join(output_dir, "goldsrc", lua_filename)
        if os.path.exists(lua_path_r) and lua_local_path:
            shutil.copy(lua_path_r, lua_path_w)
            class_requires.append(f"require('goldsrc/{classname}')")

    # Set template variables
    template_variables = {
        "$LEVELNAME":        levelname,
        "$LEVELUNAME":       leveluname,
        "$ENTITIES":         entities_lua,
        "$REGISTER_OBJECTS": collect_register_objects(output_dir),
        "$AABBS":            get_aabbs(os.path.join("output", levelname, "aabb.lua")),
        "$CLASS_REQUIRES":   '\n'.join(class_requires)
    }

    # Generate lua files from templates
    for lua_file_s in template_files:
        lua_file_r, lua_file_w = lua_file_s
        # Read
        with open(os.path.join(script_dir, "lua", lua_file_r), 'r', encoding='utf-8') as f:
            lua_source = f.read()

        # Replace template variables
        for k, v in template_variables.items():
            lua_source = lua_source.replace(k, v)
            lua_file_w = lua_file_w.replace(k, v)

        # Output lua file
        output_lua_filename = os.path.basename(lua_file_w)
        with open(os.path.join(output_dir, output_lua_filename), 'w', encoding='utf-8') as f:
            f.write(lua_source)

    # Process textures
    missing_png_path = os.path.join(script_dir, 'missing_texture.png')
    process_textures(output_dir, missing_png_path)

    print(f"✅ Mod generated at: {output_dir}")

if __name__ == "__main__":
    main()

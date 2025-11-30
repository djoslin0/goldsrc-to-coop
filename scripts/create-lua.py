import os
import sys
import re
import shutil
import json
from goldsrc_parse_ents import convert_entities_to_lua
from extract_clipnode_contents import extract_clipnode_contents_from_model, extract_node_and_leaves_contents, CONTENTS_WATER, CONTENTS_SOLID

# Load the template from template-main.lua
script_dir = os.path.dirname(os.path.abspath(__file__))

template_files = [
    [ 'template-main.lua', 'main.lua'],
    [ 'template-level.lua', 'a-goldsrc-$LEVELNAME.lua'],
]

subclasses = {
    'trigger_once': [ 'trigger_multiple' ],
    'func_door_rotating': [ 'func_door' ],
    'func_button': [ 'func_door' ],
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


def get_entity_aabbs(path):
    with open(path, 'r') as f:
        return f.read()

##################################################################################################

def convert_hull(hull, scalar):
    e_min = hull['mins']
    e_max = hull['maxs']

    n_hull = {}

    n_hull['mins'] = [
        e_min[0] * scalar,
        e_min[2] * scalar,
        e_max[1] * -scalar,
    ]

    n_hull['maxs'] = [
        e_max[0] * scalar,
        e_max[2] * scalar,
        e_min[1] * -scalar,
    ]

    n_planes = []
    inv_s = 1.0 / scalar

    for plane in hull['planes']:
        n = plane['normal']
        d = plane['dist']

        # Transform normal (using inverse-transpose)
        nx = n[0] * inv_s
        ny = n[2] * inv_s
        nz = -n[1] * inv_s

        # Renormalize
        length = (nx*nx + ny*ny + nz*nz) ** 0.5
        nx /= length
        ny /= length
        nz /= length

        # Dist scales with the same uniform scale
        d_new = d * scalar

        n_planes.append({
            'normal': [nx, ny, nz],
            'dist': d_new,
        })

    n_hull['planes'] = n_planes

    return n_hull

def get_water_hulls(path, bspguy_scale):
    if not os.path.exists(path):
        return ''

    def fmt_num(n):
        s = f"{n:.2f}"
        s = s.rstrip('0').rstrip('.')   # remove trailing zeros and dot
        return s

    def fmt_vec3(v):
        return f"{fmt_num(v[0])}, {fmt_num(v[1])}, {fmt_num(v[2])}"

    def fmt_plane(p):
        return f"{{ n = {{ {fmt_vec3(p['normal'])} }}, d = {fmt_num(p['dist'])} }}"

    def fmt_hulls(hulls):
        output = ''
        for hull in hulls:
            n_hull = convert_hull(hull, scalar)
            planes_str = ", ".join(fmt_plane(p) for p in n_hull['planes'])
            output += ( "        {"
                f" min = {{ {fmt_vec3(n_hull['mins'])} }},"
                f" max = {{ {fmt_vec3(n_hull['maxs'])} }},"
                f" planes = {{ {planes_str} }},\n"
                " },\n"
            )
        return output

    scalar = 100 / -bspguy_scale
    models_with_water = []
    output = ''

    # read bsp.json
    with open(path, 'r') as f:
        bsp_json = json.loads(f.read())

    # convert node and leaf hulls from root and export them
    root_hulls = extract_node_and_leaves_contents(bsp_json['nodes'], bsp_json['leaves'], 0, CONTENTS_WATER)
    output += fmt_hulls(root_hulls)

    # convert model hulls and export them
    for model_idx, model in bsp_json['models'].items():
        if model_idx == "0":
            continue

        if model_idx in models_with_water:
            continue

        nl_hulls = extract_node_and_leaves_contents(bsp_json['nodes'], bsp_json['leaves'], model['hulls'][0]['headnode'], CONTENTS_WATER)
        if len(nl_hulls) > 0:
            output += fmt_hulls(nl_hulls)
            models_with_water.append(model_idx)

        if model_idx in models_with_water:
            continue

        hulls = extract_clipnode_contents_from_model(model, CONTENTS_WATER)
        if len(hulls) > 0:
            output += fmt_hulls(hulls)
            models_with_water.append(model_idx)

    # find entities with a skin of CONTENTS_WATER and replace their CONTENTS_SOLID
    for entity_idx, entity in bsp_json['entities'].items():
        if 'keyvalues' not in entity:
            continue
        if 'skin' not in entity['keyvalues']:
            continue
        if 'model' not in entity['keyvalues']:
            continue
        if not entity['keyvalues']['model'].startswith('*'):
            continue
        if entity['keyvalues']['skin'] != str(CONTENTS_WATER):
            continue

        model_idx = entity['keyvalues']['model'].lstrip('*')
        if model_idx in models_with_water or model_idx == '0':
            continue

        model = bsp_json['models'][model_idx]

        nl_hulls = extract_node_and_leaves_contents(bsp_json['nodes'], bsp_json['leaves'], model['hulls'][0]['headnode'], CONTENTS_SOLID)
        if len(nl_hulls) > 0:
            output += fmt_hulls(nl_hulls)
            models_with_water.append(model_idx)

    return output

##################################################################################################

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
            dirs[:] = [d for d in dirs if not d.endswith('_mdl') and not d.endswith("_spr") and not d.endswith("_skybox")]
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

def collect_sprite_data(levelname):
    src_sprites_folder = os.path.join("output", levelname, "sprites")

    sprite_data = {}

    if not os.path.exists(src_sprites_folder):
        print("Warning: sprites folder not found, skipping sprite data collection.")
        return ''

    for sprite_folder in os.listdir(src_sprites_folder):
        sprite_path = os.path.join(src_sprites_folder, sprite_folder)
        if os.path.isdir(sprite_path):
            with open(sprite_path + "/sprite.json", 'r') as file:
                data = json.load(file)
            sprite_data[sprite_folder] = data['header']

    used_fields = ['type', 'texFormat', 'numframes']

    output = ''

    for k, v in sprite_data.items():
        output += f'sprites["{k}"]' + ' = {\n'
        for key, value in v.items():
            if key in used_fields:
                output += f'    ["{key}"] = {value},\n'
        output += '}\n'

    return output

def collect_skyboxes(path):
    actors_dir = os.path.join(path, 'actors')
    output = ''

    if not os.path.isdir(actors_dir):
        return output

    for folder_name in os.listdir(actors_dir):
        folder_path = os.path.join(actors_dir, folder_name)
        if os.path.isdir(folder_path) and folder_name.endswith('_skybox'):
            # Extract SKYBOXNAME by removing '_skybox'
            skybox_name = folder_name[:-7]
            output += f'        ["{skybox_name}"] = smlua_model_util_get_id("{folder_name}_geo"),\n'

    return output

def main():
    if len(sys.argv) < 4:
        print("Usage: python generate_level_script.py <levelname> <entities.txt filepath> <bspguy_scale>")
        sys.exit(1)

    levelname = sys.argv[1]
    leveluname = levelname.upper()
    entities_path = sys.argv[2]
    bspguy_scale = int(sys.argv[3])
    lua_only = int(sys.argv[4]) == 1

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
            class_requires.append(f"require('/goldsrc/{classname}')")

    # Set template variables
    template_variables = {
        "$LEVELNAME":        levelname,
        "$LEVELUNAME":       leveluname,
        "$ENTITIES":         entities_lua,
        "$REGISTER_OBJECTS": collect_register_objects(output_dir),
        "$ENT_AABBS":        get_entity_aabbs(os.path.join("output", levelname, "aabb.lua")),
        "$WATER_HULLS":      get_water_hulls(os.path.join("output", levelname, "bsp.json"), bspguy_scale),
        "$SKYBOXES":         collect_skyboxes(output_dir),
        "$CLASS_REQUIRES":   '\n'.join(class_requires),
        "$SPRITE_DATA":      collect_sprite_data(levelname),
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
    if not lua_only:
        missing_png_path = os.path.join(script_dir, 'missing_texture.png')
        process_textures(output_dir, missing_png_path)

    print(f"✅ Mod generated at: {output_dir}")

if __name__ == "__main__":
    main()

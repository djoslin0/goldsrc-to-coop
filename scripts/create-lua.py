import os
import sys
import re
from goldsrc_parse_ents import convert_entities_to_lua

# Load the template from template-main.lua
script_dir = os.path.dirname(os.path.abspath(__file__))

template_main_path = os.path.join(script_dir, "template-main.lua")
with open(template_main_path, 'r', encoding='utf-8') as f:
    template_main_lua = f.read()

template_a_goldsrc_path = os.path.join(script_dir, "template-a-goldsrc.lua")
with open(template_a_goldsrc_path, 'r', encoding='utf-8') as f:
    template_a_goldsrc_lua = f.read()


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

    # Write files
    with open(os.path.join(output_dir, "main.lua"), "w", encoding="utf-8") as f:
        f.write(template_main_lua
            .replace("$LEVELNAME", levelname)
            .replace("$LEVELUNAME", leveluname)
            .strip())

    with open(os.path.join(output_dir, "a-goldsrc.lua"), "w", encoding="utf-8") as f:
        f.write(template_a_goldsrc_lua
            .replace("$LEVELNAME", levelname)
            .replace("$LEVELUNAME", leveluname)
            .replace("$ENTITIES", convert_entities_to_lua(entities_path, bspguy_scale))
            .replace("$REGISTER_OBJECTS", collect_register_objects(output_dir))
            .strip())

    print(f"✅ Mod generated at: {output_dir}")

if __name__ == "__main__":
    main()

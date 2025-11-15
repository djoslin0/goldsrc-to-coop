import bpy
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
    for i, block in enumerate(blocks, 1):
        entity = {}
        # Find all key-value pairs like "key" "value"
        pairs = re.findall(r'"([^"]+)"\s+"([^"]*)"', block)
        for key, value in pairs:
            entity[key] = value

        entities.append(entity)

    return entities


# Example usage inside Blender
def import_entities_to_blender(filepath, scalar):
    scalar = 1 / -scalar
    entities = parse_entities(filepath)

    # Get or create "Entities" collection
    if "Entities" not in bpy.data.collections:
        entities_collection = bpy.data.collections.new("Entities")
        bpy.context.scene.collection.children.link(entities_collection)
    else:
        entities_collection = bpy.data.collections["Entities"]

    ent_index = 0
    for ent in entities:
        classname = ent.get("classname", "unknown")
        origin_str = ent.get("origin")
        origin = (0, 0, 0)
        if origin_str:
            try:
                x, y, z = map(float, origin_str.split())
                origin = (x * scalar, y * scalar, z * scalar)
            except ValueError:
                pass

        # Create an Empty in Blender for each entity
        obj = bpy.data.objects.new(f"{ent_index}#{classname}", None)
        obj.location = origin
        entities_collection.objects.link(obj)  # Link to Entities collection instead

        # Store all key/values as custom properties
        for k, v in ent.items():
            obj[k] = v
        ent_index += 1

    print("Entity import complete.")

# -----------------------
# Command-line args
# -----------------------
argv = sys.argv
if "--" in argv:
    argv = argv[argv.index("--") + 1:]
else:
    argv = []

if len(argv) < 1:
    print("Usage: blender --background --python import-all-objs.py -- FOLDER_PATH")
    sys.exit(1)

folder_path = argv[0]
entity_path = argv[1]
scalar = float(argv[2])
if not os.path.isdir(folder_path):
    print(f"Error: folder does not exist: {folder_path}")
    sys.exit(1)

# -----------------------
# Delete default objects
# -----------------------
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# -----------------------
# Import OBJ files
# -----------------------
for filename in os.listdir(folder_path):
    if filename.lower().endswith(".obj"):
        obj_path = os.path.join(folder_path, filename)
        print(f"Importing {obj_path}")
        bpy.ops.import_scene.obj(filepath=obj_path)

# -----------------------
# Parse and import entities
# -----------------------
import_entities_to_blender(entity_path, scalar)

print("✅ All OBJ files imported successfully.")

# -----------------------
# Save the Blender file
# -----------------------
blend_file_path = os.path.join(folder_path, "1-imported-objs.blend")
bpy.ops.wm.save_mainfile(filepath=blend_file_path)
print(f"Blender file saved as: {blend_file_path}")

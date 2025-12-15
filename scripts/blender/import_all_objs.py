import bpy
import os
import sys
import re
import math
import bmesh


def delete_default_objects():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    for area in bpy.data.screens["Layout"].areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.shading.type = 'MATERIAL'


def recalc_normals_for_clipnode_objects():
    # Loop through all objects in the scene
    for obj in bpy.data.objects:
        if "#clipnode#" in obj.name:
            # Make sure we're dealing with a mesh
            if obj.type == 'MESH':
                # Switch to object mode (required for bmesh updates)
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='OBJECT')

                # Get mesh data
                mesh = obj.data

                # Create a BMesh from the mesh
                bm = bmesh.new()
                bm.from_mesh(mesh)

                # Recalculate normals outside
                bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

                # Write back to the mesh
                bm.to_mesh(mesh)
                mesh.update()
                bm.free()

                print(f"Recalculated normals for object: {obj.name}")


def import_level_objs(folder_path):
    for filename in os.listdir(folder_path):
        if not filename.lower().endswith(".obj"):
            continue
        obj_path = os.path.join(folder_path, filename)

        print(f"Importing {obj_path}")
        bpy.ops.import_scene.obj(filepath=obj_path)

    recalc_normals_for_clipnode_objects()


def parse_entities(filepath):
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
    for i, block in enumerate(blocks, 1):
        entity = {}
        # Find all key-value pairs like "key" "value"
        pairs = re.findall(r'"([^"]+)"\s+"([^"]*)"', block)
        for key, value in pairs:
            entity[key] = value

        entities.append(entity)

    return entities


def import_entities(filepath, scalar):
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

        angles_str = ent.get("angles")
        angles = (0, 0, 0)
        if angles_str:
            try:
                x, y, z = map(float, angles_str.split())
                angles = (x, z, y + 90)
            except ValueError:
                pass

        # Create an Empty in Blender for each entity
        obj = bpy.data.objects.new(f"{ent_index}#{classname}", None)
        obj.location = origin
        obj.rotation_euler = (math.radians(angles[0]), math.radians(angles[1]), math.radians(angles[2]))
        entities_collection.objects.link(obj)  # Link to Entities collection instead

        # Store all key/values as custom properties
        for k, v in ent.items():
            obj[k] = v
        ent_index += 1

    print("Entity import complete.")


def stage_import_all_objs(num, folder_path, scalar):
    delete_default_objects()
    import_level_objs(folder_path)
    import_entities(folder_path + "/entities.txt", scalar)
    bpy.ops.wm.save_mainfile(filepath=os.path.join(folder_path, f"{num}-imported-objs.blend"))

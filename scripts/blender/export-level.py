import bpy
import os
import sys
import bmesh
import mathutils
import re
from mathutils import Vector

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import goldsrc_parse_entities

def append_blend_objects(blend_path, object_names=None):
    """
    Append objects from another .blend file into the current scene.
    :param blend_path: Path to the .blend file to append from
    :param object_names: Optional list of object names to append. If None, append all.
    """
    if not os.path.isfile(blend_path):
        print(f"Blend file not found: {blend_path}")
        return

    with bpy.data.libraries.load(blend_path, link=False) as (data_from, data_to):
        if object_names is None:
            # Append all objects
            data_to.objects = data_from.objects
        else:
            # Append only selected objects
            data_to.objects = [name for name in data_from.objects if name in object_names]

    # Link appended objects to the current scene collection
    for obj in data_to.objects:
        if obj is not None:
            bpy.context.scene.collection.objects.link(obj)
            print(f"Appended object: {obj.name}")


def export_object(objects_collection, area_obj, actors_folder, level_name, blender_object, entity_index, class_info):
    # --- Step 1: Find empty entity ---
    classname = blender_object.name.rsplit('#', 1)[-1]
    entity_name = f'{entity_index}#{classname}'
    entity = bpy.data.objects.get(entity_name)

    if entity is None:
        print(f"Warning: No entity found for index {entity_index} with classname {classname}")
        return

    # --- Step 2: Move empty to object center if at origin ---
    if entity.location == Vector((0.0, 0.0, 0.0)):
        # Calculate object's center of volume (average of all vertices)
        if blender_object.type == 'MESH':
            verts_world = [blender_object.matrix_world @ v.co for v in blender_object.data.vertices]
            center = sum(verts_world, Vector()) / len(verts_world)
            entity.location = center
        else:
            print(f"Warning: {blender_object.name} is not a mesh. Empty left at origin.")

    # --- Step 3: Set object origin to empty location ---
    bpy.context.view_layer.objects.active = blender_object
    bpy.ops.object.select_all(action='DESELECT')
    blender_object.select_set(True)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR', center='MEDIAN')
    
    # Move 3D cursor to entity location for origin_set
    bpy.context.scene.cursor.location = entity.location
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')

    # --- Step 4: Export object visuals ---
    for col in blender_object.users_collection:
        col.objects.unlink(blender_object)
    blender_object.parent = None
    objects_collection.objects.link(blender_object)

    bpy.ops.object.select_all(action='DESELECT')
    blender_object.select_set(True)
    bpy.context.view_layer.objects.active = blender_object

    bpy.data.scenes["Scene"].geoTexDir = f'actors/{level_name}_ent_{entity_index}'
    bpy.data.scenes["Scene"].geoCustomExport = True
    bpy.data.scenes["Scene"].geoExportPath = actors_folder
    bpy.data.scenes["Scene"].geoName = f'{level_name}_ent_{entity_index}'
    bpy.data.scenes["Scene"].geoStructName = f'{level_name}_ent_{entity_index}_geo'
    if class_info['_export_geo']:
        bpy.ops.object.sm64_export_geolayout_object()

    # --- Step 5: Export collision ---

    bpy.ops.object.select_all(action='DESELECT')
    blender_object.select_set(True)
    bpy.context.view_layer.objects.active = blender_object

    bpy.data.scenes["Scene"].colCustomExport = True
    bpy.data.scenes["Scene"].colExportPath = actors_folder
    bpy.data.scenes["Scene"].colName = f'{level_name}_ent_{entity_index}'
    if class_info['_export_col']:
        bpy.ops.object.sm64_export_collision()

    # --- Step 6: Set empty properties ---
    entity.sm64_obj_type = 'Object'
    entity.sm64_obj_model = 'E_MODEL_NONE'
    entity.sm64_obj_behaviour = 'id_bhvGoldsrcEntity'
    entity.fast64.sm64.game_object.use_individual_params = False
    entity.fast64.sm64.game_object.bparams = hex(entity_index)

    # --- Step 7: Parent empty to area ---
    for col in entity.users_collection:
        col.objects.unlink(entity)
    entity.parent = area_obj

    parent_collection = area_obj.users_collection[0] if area_obj.users_collection else bpy.context.scene.collection
    if entity.name not in parent_collection.objects:
        parent_collection.objects.link(entity)


def process_blender_objects(actors_folder, level_name):
    # Get or create "Objects" collection
    if "Objects" not in bpy.data.collections:
        objects_collection = bpy.data.collections.new("Objects")
        bpy.context.scene.collection.children.link(objects_collection)
    else:
        objects_collection = bpy.data.collections["Objects"]

    # Unhide all objects first
    for obj in bpy.data.objects:
        obj.hide_set(False)
        obj.hide_viewport = False
        obj.hide_render = False

    area_obj = bpy.data.objects.get("Area")
    if area_obj is None:
        print("Object 'Area' not found.")
        return

    # Get the collection that contains the parent object
    parent_collection = area_obj.users_collection[0] if area_obj.users_collection else None
    if parent_collection is None:
        print(f"'Area' is not in any collection. Using scene master collection.")
        parent_collection = bpy.context.scene.collection

    for obj in bpy.data.objects:
        if obj.name.startswith("M_"):
            # Remove from all collections
            for col in obj.users_collection:
                col.objects.unlink(obj)

            # Get classname and entity index
            classname = obj.name.rsplit('#', 1)[-1]
            entity_index = int(obj.name.split('#', 1)[0].rsplit('_', 1)[-1])

            # Set parent
            obj.parent = area_obj
            #obj.matrix_parent_inverse = area_obj.matrix_world.inverted()

            # Ensure object is in the parent collection
            if obj.name not in parent_collection.objects:
                parent_collection.objects.link(obj)

            # Select blender object in object mode
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

            # Export object or parent it to level's area
            if classname in goldsrc_parse_entities.parse_classes:
                export_object(objects_collection, area_obj, actors_folder, level_name, obj, entity_index, goldsrc_parse_entities.parse_classes[classname])


def triangulate_and_merge_all(threshold=1e-5):
    processed = 0

    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue

        mesh = obj.data

        # Create a BMesh from the object's mesh data
        bm = bmesh.new()
        try:
            bm.from_mesh(mesh)

            # Triangulate all faces
            if len(bm.faces) > 0:
                bmesh.ops.triangulate(bm, faces=list(bm.faces), quad_method='BEAUTY', ngon_method='BEAUTY')

            # Merge vertices by distance
            if threshold > 0.0 and len(bm.verts) > 0:
                bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=threshold)

            # Write back to mesh and update
            bm.to_mesh(mesh)
            mesh.update()

            processed += 1
            print(f"Processed object: {obj.name} (verts={len(mesh.vertices)}, faces={len(mesh.polygons)})")
        finally:
            bm.free()

    print(f"Done. Processed {processed} mesh objects.")
    return processed


def move_warpentry_to_spawn():
    """Find the info_player_start or info_player_deathmatch with the lowest index and move WarpEntry there."""
    spawn_obj = None
    lowest_index = None

    # Helper to extract number before '#' in object name
    def get_index(obj_name):
        match = re.match(r'(\d+)', obj_name.split('#', 1)[0])
        return int(match.group(1)) if match else None

    # Look for info_player_start objects
    for obj in bpy.data.objects:
        name_part = obj.name.split('#', 1)[-1]
        if name_part.startswith("info_player_start"):
            idx = get_index(obj.name)
            if idx is not None and (lowest_index is None or idx < lowest_index):
                spawn_obj = obj
                lowest_index = idx

    # If not found, look for info_player_deathmatch
    if spawn_obj is None:
        for obj in bpy.data.objects:
            name_part = obj.name.split('#', 1)[-1]
            if name_part.startswith("info_player_deathmatch"):
                idx = get_index(obj.name)
                if idx is not None and (lowest_index is None or idx < lowest_index):
                    spawn_obj = obj
                    lowest_index = idx

    if spawn_obj is None:
        print("No spawn object found (info_player_start or info_player_deathmatch).")
        return

    warp_entry = bpy.data.objects.get("WarpEntry")
    if warp_entry is None:
        print("Object 'WarpEntry' not found.")
        return

    # Move WarpEntry to spawn position
    warp_entry.location = spawn_obj.location.copy()
    warp_entry.rotation_euler = spawn_obj.rotation_euler
    print(f"WarpEntry moved to {spawn_obj.name} at {spawn_obj.location}")


def export_level(levels_folder, level_name):
    # Select 'Level'
    level_obj = bpy.data.objects.get("Level")
    bpy.ops.object.select_all(action='DESELECT')
    level_obj.select_set(True)
    bpy.context.view_layer.objects.active = level_obj

    bpy.data.scenes["Scene"].levelCustomExport = True
    bpy.data.scenes["Scene"].levelExportPath = levels_folder
    bpy.data.scenes["Scene"].levelName = level_name
    bpy.ops.object.sm64_export_level()


def calculate_aabb_lua():
    output = ''
    for obj in bpy.data.objects:
        if obj.name.startswith("M_"):
            # Parse entity index from the object name
            entity_index = int(obj.name.split('#', 1)[0].rsplit('_', 1)[-1])
            
            # Calculate world bounding box by transforming each corner
            aabb_world = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
            
            # Sm64 Scalar
            sm64_scalar = 100

            # Extract min/max coordinates
            min_x = round(min(v.x for v in aabb_world) * sm64_scalar)
            min_y = round(min(v.y for v in aabb_world) * sm64_scalar)
            min_z = round(min(v.z for v in aabb_world) * sm64_scalar)
            max_x = round(max(v.x for v in aabb_world) * sm64_scalar)
            max_y = round(max(v.y for v in aabb_world) * sm64_scalar)
            max_z = round(max(v.z for v in aabb_world) * sm64_scalar)
            
            output += f'entities[{entity_index+1}]._aabb = {{ min = {{ {min_x}, {min_z}, {-max_y} }}, max = {{ {max_x}, {max_z}, {-min_y} }} }}\n'

    return output

def main():
    # -----------------------
    # Get .blend file from command-line arguments
    # -----------------------
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]  # keep argv as a list
    else:
        argv = []

    if len(argv) < 1:
        print("Usage: blender --background --python export-level.py -- BLEND_FILE LEVEL_NAME APPEND_BLEND")
        sys.exit(1)

    # grab commandline params
    blend_file_path = argv[0]
    level_name = argv[1]
    append_file_path = argv[2]

    # grab folder
    folder = os.path.dirname(blend_file_path)
    if not os.path.isfile(blend_file_path):
        print(f"Error: .blend file does not exist: {blend_file_path}")
        sys.exit(1)

    # Open the .blend file
    bpy.ops.wm.open_mainfile(filepath=blend_file_path)

    # Append objects from another .blend file
    append_blend_objects(append_file_path)

    # Make directory at folder/mod and folder/mod/levels if they don't exist
    mod_folder = os.path.join(folder, "mod")
    levels_folder = os.path.join(mod_folder, "levels")
    os.makedirs(levels_folder, exist_ok=True)
    actors_folder = os.path.join(mod_folder, "actors")
    os.makedirs(actors_folder, exist_ok=True)

    # Setup export settings
    bpy.data.scenes["Scene"].exportHiddenGeometry = False
    bpy.data.scenes["Scene"].saveTextures = True
    bpy.data.scenes["Scene"].ignoreTextureRestrictions = True

    # Triangulate and merge all meshes
    triangulate_and_merge_all()

    # Perform reparenting and exporting
    process_blender_objects(actors_folder, level_name)

    move_warpentry_to_spawn()

    # Export AABBs
    with open(os.path.join(folder, "aabb.lua"), 'w') as f:
        f.write(calculate_aabb_lua())

    # Export level
    export_level(levels_folder, level_name)

    # -----------------------
    # Save to new file
    # -----------------------
    save_path = os.path.join(folder, "7-export.blend")
    bpy.ops.wm.save_mainfile(filepath=save_path)
    print(f"Blender file saved: {save_path}")


if __name__ == "__main__":
    main()


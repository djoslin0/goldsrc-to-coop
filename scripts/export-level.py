import bpy
import os
import sys
import bmesh

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

def reparent_m_objects():
    # Unhide all objects first
    for obj in bpy.data.objects:
        obj.hide_set(False)
        obj.hide_viewport = False
        obj.hide_render = False

    parent_obj = bpy.data.objects.get("Area")
    if parent_obj is None:
        print("Object 'Area' not found.")
        return

    # Get the collection that contains the parent object
    parent_collection = parent_obj.users_collection[0] if parent_obj.users_collection else None
    if parent_collection is None:
        print(f"'Area' is not in any collection. Using scene master collection.")
        parent_collection = bpy.context.scene.collection

    for obj in bpy.data.objects:
        if obj.name.startswith("M_"):
            # Set parent
            obj.parent = parent_obj
            obj.matrix_parent_inverse = parent_obj.matrix_world.inverted()

            # Remove from all collections except the parent collection
            for col in obj.users_collection:
                if col != parent_collection:
                    col.objects.unlink(obj)

            # Ensure object is in the parent collection
            if obj.name not in parent_collection.objects:
                parent_collection.objects.link(obj)

            print(f"{obj.name} parented to {parent_obj.name} and placed in {parent_collection.name}")

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
    """Find an info_player_start or info_player_deathmatch and move WarpEntry there."""
    spawn_obj = None

    # Look for info_player_start
    for obj in bpy.data.objects:
        if obj.name.startswith("info_player_start"):
            spawn_obj = obj
            break

    # If not found, look for info_player_deathmatch
    if spawn_obj is None:
        for obj in bpy.data.objects:
            if obj.name.startswith("info_player_deathmatch"):
                spawn_obj = obj
                break

    if spawn_obj is None:
        print("No spawn object found (info_player_start or info_player_deathmatch).")
        return

    warp_entry = bpy.data.objects.get("WarpEntry")
    if warp_entry is None:
        print("Object 'WarpEntry' not found.")
        return

    # Move WarpEntry to spawn position
    warp_entry.location = spawn_obj.location.copy()
    print(f"WarpEntry moved to {spawn_obj.name} at {spawn_obj.location}")

def export_level(levels_folder, level_name):
    # Select 'Level'
    level_obj = bpy.data.objects.get("Level")
    bpy.ops.object.select_all(action='DESELECT')
    level_obj.select_set(True)
    bpy.context.view_layer.objects.active = level_obj

    bpy.data.scenes["Scene"].exportHiddenGeometry = False
    bpy.data.scenes["Scene"].saveTextures = True
    bpy.data.scenes["Scene"].ignoreTextureRestrictions = True

    bpy.data.scenes["Scene"].levelCustomExport = True
    bpy.data.scenes["Scene"].levelExportPath = levels_folder
    bpy.data.scenes["Scene"].levelName = level_name
    bpy.ops.object.sm64_export_level()

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


    blend_file_path = argv[0]
    level_name = argv[1]
    append_file_path = argv[2]

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

    # Perform reparenting
    reparent_m_objects()

    # Triangulate and merge all meshes
    triangulate_and_merge_all()

    move_warpentry_to_spawn()

    # Export level
    export_level(levels_folder, level_name)

    # -----------------------
    # Save to new file
    # -----------------------
    save_path = os.path.join(folder, "6-export.blend")
    bpy.ops.wm.save_mainfile(filepath=save_path)
    print(f"Blender file saved: {save_path}")


if __name__ == "__main__":
    main()


import bpy
import os
import sys

def is_in_mdl_collection(obj):
    for coll in obj.users_collection:
        if coll.name == 'MDL':
            return True
    return False

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
        print("Usage: blender --background --python coop-lightmap.py -- BLEND_FILE")
        sys.exit(1)

    blend_file_path = argv[0]
    if not os.path.isfile(blend_file_path):
        print(f"Error: .blend file does not exist: {blend_file_path}")
        sys.exit(1)

    # Open the .blend file
    bpy.ops.wm.open_mainfile(filepath=blend_file_path)

    # -----------------------
    # Material processing
    # -----------------------

    # Ensure all objects are deselected first
    for obj in bpy.data.objects:
        obj.select_set(False)

    # Select all mesh objects (if your operator requires selection)
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and not is_in_mdl_collection(obj):
            obj.select_set(True)

    # Determine atlas image path (relative to blend file)
    blend_dir = os.path.dirname(bpy.data.filepath)
    atlas_path = os.path.join(blend_dir, "atlases", "atlas_0.png")
    if not os.path.isfile(atlas_path):
        raise RuntimeError(f"Atlas image not found: {atlas_path}")
    lm_image = bpy.data.images.load(atlas_path)

    # Assign to scene properties for your custom operator
    bpy.context.scene.CoopLMImage = lm_image
    bpy.context.scene.CoopAOImage = None
    bpy.context.scene.CoopAOStrength = 0
    bpy.context.scene.CoopLMFog = False
    bpy.context.scene.CoopReplaceOriginals = True

    # Select all mesh objects
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and not is_in_mdl_collection(obj):
            obj.select_set(True)

    # Ensure there is an active mesh object
    active_obj = None
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and not is_in_mdl_collection(obj):
            active_obj = obj
            break

    if active_obj is None:
        raise RuntimeError("No mesh objects found to set as active for f3d_convert_uvs")

    bpy.context.view_layer.objects.active = active_obj

    # Run your custom operator
    bpy.ops.object.f3d_convert_uvs()

    # ----------------------
    # convert MDL materials
    # ----------------------

    bpy.data.scenes["Scene"].bsdf_conv_all = False

    for obj in bpy.data.objects:
        obj.select_set(False)

    for obj in bpy.data.objects:
        if not is_in_mdl_collection(obj):
            continue
        obj.select_set(True)
        bpy.ops.object.convert_bsdf()
        obj.select_set(False)


    # -----------------------
    # Save to new file
    # -----------------------
    folder = os.path.dirname(blend_file_path)
    save_path = os.path.join(folder, "5-coop-lightmap.blend")
    bpy.ops.wm.save_mainfile(filepath=save_path)
    print(f"Blender file saved: {save_path}")


if __name__ == "__main__":
    main()

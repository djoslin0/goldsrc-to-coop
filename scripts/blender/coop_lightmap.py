import bpy
import os
import sys


def process_materials():
    # Ensure all objects are deselected first
    for obj in bpy.data.objects:
        obj.select_set(False)

    # Select all mesh objects (if your operator requires selection)
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            obj.select_set(True)

    # Determine atlas image path (relative to blend file)
    blend_dir = os.path.dirname(bpy.data.filepath)
    atlas_dir = os.path.join(blend_dir, "atlases")
    png_files = [f for f in os.listdir(atlas_dir) if f.lower().endswith('.png')]
    if not png_files:
        raise RuntimeError("No PNG files found in atlas directory")
    png_files.sort(key=str.lower)
    atlas_filename = png_files[0]
    atlas_path = os.path.join(atlas_dir, atlas_filename)
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
        if obj.type == 'MESH':
            obj.select_set(True)

    # Ensure there is an active mesh object
    active_obj = None
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            active_obj = obj
            break

    if active_obj is None:
        raise RuntimeError("No mesh objects found to set as active for f3d_convert_uvs")

    bpy.context.view_layer.objects.active = active_obj

    # Run your custom operator
    bpy.ops.object.f3d_convert_uvs()


def stage_coop_lightmap(num, folder):
    process_materials()
    bpy.ops.wm.save_mainfile(filepath=os.path.join(folder, f"{num}-coop-lightmap.blend"))

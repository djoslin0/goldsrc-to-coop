import bpy
import os
import sys

def is_in_mdl_collection(obj):
    for coll in obj.users_collection:
        if coll.name == 'MDL':
            return True
    return False


def process_materials():
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


def convert_mdl_materials():
    # Convert materials object-by-object
    bpy.data.scenes["Scene"].bsdf_conv_all = False

    # Store every mdl_flag per obj, per material slot
    mdl_flags = {}

    # Deselect all
    for obj in bpy.data.objects:
        obj.select_set(False)
        mdl_flags[obj] = []

    # Store mdl flags
    for obj in bpy.data.objects:
        for slot in obj.material_slots:
            mat = slot.material
            if not mat or not mat.use_nodes:
                continue
            bsdf_node = mat.node_tree.nodes.get('Principled BSDF')
            if not bsdf_node:
                continue
            ior = bsdf_node.inputs['IOR'].default_value
            mdl_flags[obj].append(int(ior))

    # Convert to fast64 mats and remember mdl flags
    for obj in bpy.data.objects:
        if not is_in_mdl_collection(obj):
            continue

        obj.select_set(True)
        bpy.ops.object.convert_bsdf()
        obj.select_set(False)

        for i, slot in enumerate(obj.material_slots):
            mat = slot.material
            mat['mdl_flags'] = mdl_flags[obj][i]


def stage_coop_lightmap(num, folder):
    process_materials()
    convert_mdl_materials()
    bpy.ops.wm.save_mainfile(filepath=os.path.join(folder, f"{num}-coop-lightmap.blend"))

import bpy
import os
import json
import re
import math
import set_fast64_stuff
import export_level
from mathutils import Vector

# mdl flags
STUDIO_NF_FLATSHADE  = 0x0001
STUDIO_NF_CHROME     = 0x0002
STUDIO_NF_FULLBRIGHT = 0x0004
STUDIO_NF_NOMIPS     = 0x0008
STUDIO_NF_ALPHA      = 0x0010
STUDIO_NF_ADDITIVE   = 0x0020
STUDIO_NF_MASKED     = 0x0040
STUDIO_NF_UV_COORDS  = (1<<31)


mdl_jsons = {}

def get_root_name(obj):
    while obj.parent:
        obj = obj.parent
    return obj.name

def is_in_mdl_collection(obj):
    for coll in obj.users_collection:
        if coll.name == 'MDL':
            return True
    return False

def import_mdl(subdir_path, mdl_collection):
    empty_name = os.path.basename(subdir_path)

    json_path = os.path.join(subdir_path, "mdl.json")
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            mdl_jsons[empty_name] = json.load(f)

    # Create empty object
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    mdl_root = bpy.context.active_object
    mdl_root.name = empty_name
    mdl_collection.objects.link(mdl_root)
    if mdl_root.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(mdl_root)

    # Add an empty called switch_node
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    switch_node = bpy.context.active_object
    switch_node.name = "a_switch"
    switch_node.sm64_obj_type = "Switch"
    switch_node.switchFunc = "geo_switch_anim_state"
    switch_node.parent = mdl_root
    mdl_collection.objects.link(switch_node)
    if switch_node.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(switch_node)

    # Add an empty to fix the following switch
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    aaa_null = bpy.context.active_object
    aaa_null.name = 'aaa_null'
    aaa_null.parent = switch_node
    mdl_collection.objects.link(aaa_null)
    if aaa_null.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(aaa_null)

    # Get all .obj files in subdir
    obj_files = [f for f in os.listdir(subdir_path) if f.lower().endswith('.obj')]

    imported_objects = []
    for filename in obj_files:
        obj_path = os.path.join(subdir_path, filename)
        print(f"Importing MDL body {obj_path}")

        # Capture selected before import
        prev_selected = set(bpy.context.selected_objects)

        # Import OBJ
        bpy.ops.import_scene.obj(filepath=obj_path)

        # Get newly imported objects
        new_objs = [obj for obj in bpy.context.selected_objects if obj not in prev_selected]
        imported_objects.extend(new_objs)

        # Link each imported object to MDL collection
        index = 0
        for obj in new_objs:
            obj.name = f"{os.path.basename(obj_path)}_{index:03d}"
            index = index + 1
            obj.parent = switch_node
            if obj.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(obj)
            mdl_collection.objects.link(obj)

    switch_node.switchParam = len(imported_objects)

    # Deselect all
    bpy.ops.object.select_all(action='DESELECT')


def import_mdls(folder_path):
    mdl_folder = os.path.join(folder_path, "mdl_models")
    if not os.path.isdir(mdl_folder):
        return

    # Get or create "MDL" collection
    if "MDL" not in bpy.data.collections:
        mdl_collection = bpy.data.collections.new("MDL")
        bpy.context.scene.collection.children.link(mdl_collection)
    else:
        mdl_collection = bpy.data.collections["MDL"]

    # Iterate through subdirectories in the mdl_models folder
    for subdir in os.listdir(mdl_folder):
        subdir_path = os.path.join(mdl_folder, subdir)
        if os.path.isdir(subdir_path):
            import_mdl(subdir_path, mdl_collection)


def convert_mdl_materials():
    # Convert materials object-by-object
    bpy.data.scenes["Scene"].bsdf_conv_all = False

    # Convert to fast64 mats
    for obj in bpy.data.objects:
        if not is_in_mdl_collection(obj):
            continue
        if obj.type != 'MESH':
            continue
        obj.select_set(True)
        bpy.ops.object.convert_bsdf()
        obj.select_set(False)


def apply_material_flags_to_objects():
    for obj in bpy.data.objects:
        # Only check objects that have material slots
        if not hasattr(obj, "material_slots"):
            continue

        root_name = get_root_name(obj)
        json_data = mdl_jsons.get(root_name, {})
        textures = json_data.get('textures', {})

        # check for and apply mdl_flags
        for slot in obj.material_slots:
            mat = slot.material
            if not mat or not mat.name:
                continue

            base_name = re.sub(r'(\.\d+)?_f3d$', '', mat.name)
            mdl_flags = textures.get(base_name, {}).get('flags', 0)
            mat['mdl_flags'] = mdl_flags

            if (mdl_flags & STUDIO_NF_ALPHA) != 0:
                set_fast64_stuff.set_fast64_material_render_mode_texture(mat, 128)
            elif (mdl_flags & STUDIO_NF_ADDITIVE) != 0:
                set_fast64_stuff.set_fast64_material_render_mode_additive(mat, 128)
            elif (mdl_flags & STUDIO_NF_MASKED) != 0:
                set_fast64_stuff.set_fast64_material_render_mode_solid(mat, False)

            if (mdl_flags & STUDIO_NF_FLATSHADE) == 0:
                set_fast64_stuff.set_faces_smooth_for_material(obj, mat)


def shift_uvs_into_unit_range(obj):
    """
    Attempts to shift each triangle's UVs so they fit into the [0,1] range,
    using integer wrapping offsets. Does NOT scale UVs.
    """
    mesh = obj.data

    if not mesh.uv_layers.active:
        raise RuntimeError(f"Object '{obj.name}' has no UV layers!")

    uv_layer = mesh.uv_layers.active.data

    def can_shift_into_unit(uvs, shift):
        """Check if shifting all UVs by 'shift' will place them in [0,1]."""
        for uv in uvs:
            shifted = uv - shift
            if not (0.0 <= shifted.x <= 1.0 and 0.0 <= shifted.y <= 1.0):
                return False
        return True

    for poly in mesh.polygons:
        if len(poly.loop_indices) != 3:
            continue  # only triangles

        loop_idxs = poly.loop_indices
        uvs = [uv_layer[i].uv.copy() for i in loop_idxs]

        # Compute the rounded average for base integer shift
        avg = sum(uvs, Vector((0.0, 0.0))) / 3.0
        base_shift = Vector((round(avg.x), round(avg.y)))

        # Try the base shift first
        shift_to_use = None

        if can_shift_into_unit(uvs, base_shift):
            shift_to_use = base_shift
        else:
            # Try small integer offsets around that shift (3×3 area)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    test_shift = base_shift + Vector((dx, dy))
                    if can_shift_into_unit(uvs, test_shift):
                        shift_to_use = test_shift
                        break
                if shift_to_use:
                    break

        # Apply shift if one fits the 0..1 range
        if shift_to_use:
            for i in loop_idxs:
                uv_layer[i].uv -= shift_to_use

    mesh.update()


def shift_mdl_uvs_into_unit_range():
    """Shift UVs into unit range for all MDL mesh objects."""
    for obj in bpy.data.objects:
        if not is_in_mdl_collection(obj):
            continue
        if obj.type != 'MESH':
            continue

        try:
            shift_uvs_into_unit_range(obj)
        except RuntimeError as e:
            print(f"Warning: Could not shift UVs for object '{obj.name}': {e}")


def export_mdl(obj, actors_folder):
    # Select blender object in object mode
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    bpy.data.scenes["Scene"].geoTexDir = f'actors/{obj.name}'
    bpy.data.scenes["Scene"].geoCustomExport = True
    bpy.data.scenes["Scene"].geoExportPath = actors_folder
    bpy.data.scenes["Scene"].geoName = f'{obj.name}'
    bpy.data.scenes["Scene"].geoStructName = f'{obj.name}_geo'
    bpy.ops.object.sm64_export_geolayout_object()

def wipe_scene():
    # delete objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def stage_convert_mdls(folder):
    # create new blend file
    wipe_scene()

    # get / create folder
    mod_folder = os.path.join(folder, "mod")
    actors_folder = os.path.join(mod_folder, "actors")
    os.makedirs(actors_folder, exist_ok=True)

    import_mdls(folder)
    export_level.triangulate_and_merge_all()

    convert_mdl_materials()
    apply_material_flags_to_objects()

    shift_mdl_uvs_into_unit_range()

    # Export only the root empty objects (not the child meshes)
    for obj in bpy.data.objects:
        if not is_in_mdl_collection(obj):
            continue
        if obj.parent:
            continue
        export_mdl(obj, actors_folder)

    # Save to new file
    bpy.ops.wm.save_mainfile(filepath=os.path.join(folder, f"z-convert-mdls.blend"))

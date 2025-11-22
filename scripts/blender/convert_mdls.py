import bpy
import os

import set_fast64_stuff
import export_level

# mdl flags
STUDIO_NF_FLATSHADE  = 0x0001
STUDIO_NF_CHROME     = 0x0002
STUDIO_NF_FULLBRIGHT = 0x0004
STUDIO_NF_NOMIPS     = 0x0008
STUDIO_NF_ALPHA      = 0x0010
STUDIO_NF_ADDITIVE   = 0x0020
STUDIO_NF_MASKED     = 0x0040
STUDIO_NF_UV_COORDS  = (1<<31)


def is_in_mdl_collection(obj):
    for coll in obj.users_collection:
        if coll.name == 'MDL':
            return True
    return False


def import_mdl_objs(folder_path):
    mdl_folder = os.path.join(folder_path, "mdl_models")
    if not os.path.isdir(mdl_folder):
        return

    # Get or create "MDL" collection
    if "MDL" not in bpy.data.collections:
        mdl_collection = bpy.data.collections.new("MDL")
        bpy.context.scene.collection.children.link(mdl_collection)
    else:
        mdl_collection = bpy.data.collections["MDL"]

    # Iterate through files in the mdl_models subfolder
    for filename in os.listdir(mdl_folder):
        # Skip files that are not .obj files
        if not filename.lower().endswith(".obj"):
            continue

        # Construct full path to the .obj file
        obj_path = os.path.join(mdl_folder, filename)

        # Print import status
        print(f"Importing MDL {obj_path}")

        # Capture selected objects before import to identify newly imported ones
        prev_selected = set(bpy.context.selected_objects)

        # Import the OBJ file using Blender's operator
        bpy.ops.import_scene.obj(filepath=obj_path)

        # Determine which objects were imported by checking selection difference
        imported_objects = [obj for obj in bpy.context.selected_objects if obj not in prev_selected]

        # Move imported objects to the MDL collection
        for obj in imported_objects:
            # Unlink from scene collection if linked
            if obj.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(obj)
            # Link to the MDL collection
            mdl_collection.objects.link(obj)


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


def apply_material_flags_to_objects():
    for obj in bpy.data.objects:
        # Only check objects that have material slots
        if not hasattr(obj, "material_slots"):
            continue

        # check for and apply mdl_flags
        for slot in obj.material_slots:
            mat = slot.material
            if not mat or 'mdl_flags' not in mat:
                continue
            mdl_flags = mat['mdl_flags']
            if (mdl_flags & STUDIO_NF_ALPHA) != 0:
                set_fast64_stuff.set_fast64_material_render_mode_texture(mat, 128)
            elif (mdl_flags & STUDIO_NF_ADDITIVE) != 0:
                set_fast64_stuff.set_fast64_material_render_mode_additive(mat, 128)
            elif (mdl_flags & STUDIO_NF_MASKED) != 0:
                set_fast64_stuff.set_fast64_material_render_mode_solid(mat, False)

            if (mdl_flags & STUDIO_NF_FLATSHADE) == 0:
                set_fast64_stuff.set_faces_smooth_for_material(obj, mat)


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

    import_mdl_objs(folder)
    export_level.triangulate_and_merge_all()

    convert_mdl_materials()
    apply_material_flags_to_objects()

    for obj in bpy.data.objects:
        if not is_in_mdl_collection(obj):
            continue
        export_mdl(obj, actors_folder)

    # Save to new file
    bpy.ops.wm.save_mainfile(filepath=os.path.join(folder, f"z-convert-mdls.blend"))


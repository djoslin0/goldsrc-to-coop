import bpy
import os
import sys
import re

ignore_collision_classes = [
    "func_illusionary",
    "func_water",
    # common
    "func_vehiclecontrols",
    "func_tankcontrols",
    "func_bomb_target",
    "func_hostage_rescue",
    "func_buyzone",
    "func_areaportal",
    "func_monsterclip",
    "func_clip_vphysics",
    "env_bubbles",
    "trigger_push",
]

ignore_render_classes = [
    "func_clip",
    # common
    "func_vehiclecontrols",
    "func_tankcontrols",
    "func_bomb_target",
    "func_hostage_rescue",
    "func_buyzone",
    "func_areaportal",
    "func_monsterclip",
    "func_clip_vphysics",
    "env_bubbles",
    "trigger_push",
]

invisible_mat_names = [
    "null_f3d",
    "sky_f3d",
    "sky_LM",
    "aaatrigger"
]


def is_invisible_mat(name):
    for i in invisible_mat_names:
        if name.lower().startswith(i):
            return True
    return False


def update_material_cache(mat):
    # Update the material's cache using context override
    override = bpy.context.copy()
    override['material'] = mat
    with bpy.context.temp_override(**override):
        bpy.ops.material.update_f3d_nodes()


def check_image_has_transparency(image):
    if image.channels != 4:
        return False  # No alpha channel
    pixels = list(image.pixels)
    # Check alpha values (every 4th value starting from index 3)
    for i in range(3, len(pixels), 4):
        if pixels[i] < 1.0:
            return True
    return False


def load_additive_image(tex):
    if not tex or not tex.filepath:
        return tex

    # Construct the additive filepath
    additive_filepath = tex.filepath.replace('.png', '_additive.png')

    # Check if additive image is already loaded
    additive_image = bpy.data.images.get(os.path.basename(additive_filepath))
    if additive_image:
        return additive_image

    # Load the additive image if not already loaded
    try:
        additive_image = bpy.data.images.load(additive_filepath)
        return additive_image
    except RuntimeError:
        print(f"Warning: Could not load additive image {additive_filepath}, using original")
        return tex


def set_fast64_material_invisible(mat):
    mat.f3d_mat.draw_layer.sm64 = '4'
    mat.f3d_mat.combiner1.D_alpha = '0'
    mat.collision_type_simple = 'Custom'
    mat.collision_custom = '0x100'
    update_material_cache(mat)


def set_fast64_material_render_mode_color(mat, color, alpha):
    # TODO: additive
    mat.f3d_mat.draw_layer.sm64 = '5'
    mat.f3d_mat.combiner1.A = 'PRIMITIVE'
    mat.f3d_mat.combiner1.C = 'TEXEL0'
    mat.f3d_mat.combiner1.D_alpha = 'PRIMITIVE'
    mat.f3d_mat.rdp_settings.g_cull_back = False
    mat.f3d_mat.prim_color = (color[0]/255, color[1]/255, color[2]/255, alpha/255)
    update_material_cache(mat)


def set_fast64_material_render_mode_texture(mat, alpha):
    mat.f3d_mat.draw_layer.sm64 = '5'
    mat.f3d_mat.combiner1.A = '0'
    mat.f3d_mat.combiner1.B = '0'
    mat.f3d_mat.combiner1.C = '0'
    mat.f3d_mat.combiner1.D = 'TEXEL0'
    mat.f3d_mat.combiner1.D_alpha = 'TEXEL0' if check_image_has_transparency(mat.f3d_mat.tex0.tex) else 'PRIMITIVE'
    mat.f3d_mat.prim_color = (1.0, 1.0, 1.0, alpha/255)
    update_material_cache(mat)


def set_fast64_material_render_mode_glow(mat, alpha):
    # TODO: additive
    set_fast64_material_render_mode_additive(mat, alpha)


def set_fast64_material_render_mode_solid(mat, cull_back = True):
    mat.f3d_mat.draw_layer.sm64 = '4'
    mat.f3d_mat.combiner1.D_alpha = 'TEXEL0'
    mat.f3d_mat.rdp_settings.g_cull_back = cull_back
    update_material_cache(mat)


def set_fast64_material_water(mat):
    mat.collision_type_simple = "SURFACE_WATER"
    mat.f3d_mat.rdp_settings.g_cull_back = False


def set_fast64_material_render_mode_additive(mat, alpha):
    tex = mat.f3d_mat.tex0.tex
    mat.f3d_mat.tex0.tex = load_additive_image(tex)
    update_material_cache(mat)

    mat.f3d_mat.draw_layer.sm64 = '5'
    mat.f3d_mat.combiner1.A = '0'
    mat.f3d_mat.combiner1.B = '0'
    mat.f3d_mat.combiner1.C = '0'
    mat.f3d_mat.combiner1.D = 'TEXEL0'
    mat.f3d_mat.combiner1.D_alpha = 'TEXEL0'

    #mat.f3d_mat.rdp_settings.g_cull_back = False


def set_faces_smooth_for_material(obj, mat):
    if obj.type != 'MESH':
        return
    for i, slot in enumerate(obj.material_slots):
        if slot.material == mat:
            for polygon in obj.data.polygons:
                if polygon.material_index == i:
                    polygon.use_smooth = True
            break


def apply_brush_types_to_objects():
    for obj in bpy.data.objects:
        obj_name = obj.name

        # Check if '#' exists in the name
        if '#' in obj_name:
            brush_type = obj_name.rsplit('#', 1)[1]

            # Store brush_type as a custom property (optional)
            obj["brush_type"] = brush_type

            if brush_type in ignore_collision_classes:
                obj["ignore_collision"] = True

            if brush_type in ignore_render_classes:
                obj["ignore_render"] = True

            # check for other flags
            if obj_name.startswith("M_"):
                try:
                    entity_index = int(re.search(r'ENT_(\d+)#', obj_name).group(1))
                    entity_obj = next((o for o in bpy.data.objects if o.name.startswith(f"{entity_index}#")), None)
                    if entity_obj and entity_obj["zhlt_noclip"] and str(entity_obj["zhlt_noclip"]) == "1":
                        obj["ignore_collision"] = True
                    if entity_obj and entity_obj["zhlt_invisible"] and str(entity_obj["zhlt_invisible"]) == "1":
                        obj["ignore_render"] = True
                except Exception as ex:
                    pass

        else:
            # No '#' found
            obj["brush_type"] = None


def apply_invisible_materials_to_objects():
    for obj in bpy.data.objects:
        # Only check objects that have material slots
        if not hasattr(obj, "material_slots"):
            continue

        # replace sky/null textures
        for slot in obj.material_slots:
            mat = slot.material
            if mat and is_invisible_mat(mat.name):
                set_fast64_material_invisible(mat)


def apply_rendermode_to_objects():
    for obj in bpy.data.objects:
        # Only check objects that have material slots
        if not hasattr(obj, "material_slots"):
            continue

        # set rendermode
        try:
            obj_name = obj.name
            entity_index = int(re.search(r'ENT_(\d+)#', obj_name).group(1))
            entity_obj = next((o for o in bpy.data.objects if o.name.startswith(f"{entity_index}#")), None)
            entity_rendermode = int(entity_obj.get("rendermode") or 0)
            entity_renderamt = int(entity_obj.get("renderamt") or 255)
            entity_rendercolor = list(map(int, (entity_obj.get("rendercolor") or "255 255 255").split()))
        except Exception as ex:
            continue

        is_water = 'brush_type' in obj and obj['brush_type'] == "func_water"
        is_water = is_water or obj.name.endswith('#worldspawn_liquid')

        if entity_rendermode == 0 and not is_water:
            continue

        ignore_collision = "ignore_collision" in obj and obj["ignore_collision"]

        # duplicate and alter materials for rendermode
        for i, slot in enumerate(obj.material_slots):
            if not slot.material:
                continue
            if is_invisible_mat(slot.material.name):
                continue

            new_mat = slot.material.copy()
            obj.material_slots[i].material = new_mat

            if entity_rendermode == 1:
                set_fast64_material_render_mode_color(new_mat, entity_rendercolor, entity_renderamt)
            elif entity_rendermode == 2:
                set_fast64_material_render_mode_texture(new_mat, entity_renderamt)
            elif entity_rendermode == 3:
                set_fast64_material_render_mode_glow(new_mat, entity_renderamt)
            elif entity_rendermode == 4:
                set_fast64_material_render_mode_solid(new_mat, not ignore_collision)
            elif entity_rendermode == 5:
                set_fast64_material_render_mode_additive(new_mat, entity_renderamt)

            if is_water:
                set_fast64_material_water(new_mat)


def stage_set_fast64_stuff(num, folder):
    bpy.data.scenes["Scene"].f3d_simple = False

    apply_brush_types_to_objects()
    apply_invisible_materials_to_objects()
    apply_rendermode_to_objects()

    bpy.ops.wm.save_mainfile(filepath=os.path.join(folder, f"{num}-set-fast64.blend"))

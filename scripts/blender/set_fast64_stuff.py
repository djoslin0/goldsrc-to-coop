import bpy
import os
import sys
import re

trigger_names = [
    "func_vehiclecontrols",
    "func_tankcontrols",
    "func_bomb_target",
    "func_hostage_rescue",
    "func_buyzone",
    "func_areaportal",
    "func_monsterclip",
    "func_clip_vphysics",
    "env_bubbles",
]


invisible_mat_names = [
    "null_f3d",
    "sky_f3d",
    "sky_LM"
]


# mdl flags
STUDIO_NF_FLATSHADE  = 0x0001
STUDIO_NF_CHROME     = 0x0002
STUDIO_NF_FULLBRIGHT = 0x0004
STUDIO_NF_NOMIPS     = 0x0008
STUDIO_NF_ALPHA      = 0x0010
STUDIO_NF_ADDITIVE   = 0x0020
STUDIO_NF_MASKED     = 0x0040
STUDIO_NF_UV_COORDS  = (1<<31)


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


def set_fast64_material_invisible(mat):
    mat.f3d_mat.draw_layer.sm64 = '4'
    mat.f3d_mat.combiner1.D_alpha = '0'
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
    mat.f3d_mat.combiner1.D_alpha = 'PRIMITIVE'
    mat.f3d_mat.prim_color = (1.0, 1.0, 1.0, alpha/255)
    update_material_cache(mat)


def set_fast64_material_render_mode_glow(mat, alpha):
    # TODO: additive
    set_fast64_material_render_mode_texture(mat, alpha)
    mat.f3d_mat.rdp_settings.g_cull_back = False
    update_material_cache(mat)


def set_fast64_material_render_mode_solid(mat, cull_back = True):
    mat.f3d_mat.draw_layer.sm64 = '4'
    mat.f3d_mat.combiner1.D_alpha = 'TEXEL0'
    mat.f3d_mat.rdp_settings.g_cull_back = cull_back
    update_material_cache(mat)


def set_fast64_material_render_mode_additive(mat, alpha):
    # TODO: additive
    set_fast64_material_render_mode_texture(mat, alpha)
    mat.f3d_mat.rdp_settings.g_cull_back = False
    update_material_cache(mat)


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

            if brush_type == "func_illusionary":
                obj["ignore_collision"] = True
            elif brush_type == "func_clip":
                obj["ignore_render"] = True
            elif brush_type in trigger_names or brush_type.startswith('trigger_'):
                obj["ignore_render"] = True
                obj["ignore_collision"] = True
                #obj.hide_viewport = True
        else:
            # No '#' found
            obj["brush_type"] = None


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
                set_fast64_material_render_mode_texture(mat, 128)
            elif (mdl_flags & STUDIO_NF_ADDITIVE) != 0:
                set_fast64_material_render_mode_additive(mat, 128)
            elif (mdl_flags & STUDIO_NF_MASKED) != 0:
                set_fast64_material_render_mode_solid(mat, False)

            if (mdl_flags & STUDIO_NF_FLATSHADE) == 0:
                set_faces_smooth_for_material(obj, mat)


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
            entity_rendermode = int(entity_obj.get("rendermode"))
            entity_renderamt = int(entity_obj.get("renderamt"))
            entity_rendercolor = list(map(int, entity_obj.get("rendercolor").split()))
        except Exception as ex:
            continue

        if entity_rendermode == 0:
            continue

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
                set_fast64_material_render_mode_solid(new_mat)
            elif entity_rendermode == 5:
                set_fast64_material_render_mode_additive(new_mat, entity_renderamt)


def stage_set_fast64_stuff(num, folder):
    bpy.data.scenes["Scene"].f3d_simple = False

    apply_brush_types_to_objects()
    apply_material_flags_to_objects()
    apply_invisible_materials_to_objects()
    apply_rendermode_to_objects()

    bpy.ops.wm.save_mainfile(filepath=os.path.join(folder, f"{num}-set-fast64.blend"))

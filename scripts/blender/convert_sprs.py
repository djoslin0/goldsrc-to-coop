import bpy
import json
import math
import convert_mdls
import os
import set_fast64_stuff

def set_fast64_material_spr_opaque(mat):
    mat.f3d_mat.draw_layer.sm64 = '1'

    mat.f3d_mat.combiner1.A = 'ENVIRONMENT'
    mat.f3d_mat.combiner1.B = '0'
    mat.f3d_mat.combiner1.C = 'TEXEL0'
    mat.f3d_mat.combiner1.D = '0'

    mat.f3d_mat.combiner1.A_alpha = '1'
    mat.f3d_mat.combiner1.B_alpha = '0'
    mat.f3d_mat.combiner1.C_alpha = 'ENVIRONMENT'
    mat.f3d_mat.combiner1.D_alpha = '0'

    mat.f3d_mat.rdp_settings.g_cull_back = False
    set_fast64_stuff.update_material_cache(mat)

def set_fast64_material_spr_cutout(mat):
    mat.f3d_mat.draw_layer.sm64 = '4'

    mat.f3d_mat.combiner1.A = 'ENVIRONMENT'
    mat.f3d_mat.combiner1.B = '0'
    mat.f3d_mat.combiner1.C = 'TEXEL0'
    mat.f3d_mat.combiner1.D = '0'

    mat.f3d_mat.combiner1.A_alpha = 'ENVIRONMENT'
    mat.f3d_mat.combiner1.B_alpha = '0'
    mat.f3d_mat.combiner1.C_alpha = 'TEXEL0'
    mat.f3d_mat.combiner1.D_alpha = '0'
    #mat.f3d_mat.combiner1.D_alpha = 'PRIMITIVE'

    #mat.f3d_mat.prim_color = (1, 1, 1, 0.15)

    mat.f3d_mat.rdp_settings.g_cull_back = False
    set_fast64_stuff.update_material_cache(mat)

def set_fast64_material_spr_alpha(mat):
    mat.f3d_mat.draw_layer.sm64 = '5'

    mat.f3d_mat.combiner1.A = 'ENVIRONMENT'
    mat.f3d_mat.combiner1.B = '0'
    mat.f3d_mat.combiner1.C = 'TEXEL0'
    mat.f3d_mat.combiner1.D = '0'

    mat.f3d_mat.combiner1.A_alpha = 'ENVIRONMENT'
    mat.f3d_mat.combiner1.B_alpha = '0'
    mat.f3d_mat.combiner1.C_alpha = 'TEXEL0'
    mat.f3d_mat.combiner1.D_alpha = '0'

    mat.f3d_mat.rdp_settings.g_cull_back = False
    set_fast64_stuff.update_material_cache(mat)

def convert_spr(src_sprites_folder, sprite_folder, actors_folder, scalar):
    # Reset the 3D cursor to the world origin
    bpy.context.scene.cursor.location = (0, 0, 0)

    sprite_data = None

    full_path = src_sprites_folder + '/' + sprite_folder

    with open(full_path + "/sprite.json", 'r') as file:
        sprite_data = json.load(file)

    if not sprite_data:
        return

    # Add an empty called sprite_root
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    sprite_root = bpy.context.active_object
    sprite_root.name = sprite_folder

    # Add an empty called a_geo_asm
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    geo_asm = bpy.context.active_object
    geo_asm.name = "a_geo_asm"
    geo_asm.sm64_obj_type = "Geo ASM"
    geo_asm.fast64.sm64.geo_asm.func = "g_goldsrc_spr"    
    geo_asm.fast64.sm64.geo_asm.param = "0"
    geo_asm.parent = sprite_root

    # Add an empty called b_display_list
    for layer in ["1", "4", "5"]:
        bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
        display_list = bpy.context.active_object
        display_list.name = f"b_display_list_{layer}"
        display_list.sm64_obj_type = "Geo Displaylist"
        display_list.draw_layer_static = layer
        display_list.dlReference = "NULL"
        display_list.parent = sprite_root

    # Add an empty called switch_node
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    switch_node = bpy.context.active_object
    switch_node.name = "c_switch"
    switch_node.sm64_obj_type = "Switch"
    switch_node.switchFunc = "geo_switch_anim_state"
    switch_node.parent = sprite_root

    # Add an empty to fix the following switch
    bpy.ops.object.empty_add(type='PLAIN_AXES', location=(0, 0, 0))
    aaa_null = bpy.context.active_object
    aaa_null.name = 'aaa_null'
    aaa_null.parent = switch_node

    # count anim states
    anim_states = 0

    # create planes
    opaque_objs = []
    for group_idx, group in enumerate(sprite_data['groups']):
        for frame_idx, frame in enumerate(group['frames']):
            # Create a plane with the specified width and height
            width = frame['width'] * scalar  # Scale down for Blender units
            height = frame['height'] * scalar
            origin_x, origin_y = frame['origin']
            origin_x = origin_x * scalar
            origin_y = origin_y * scalar

            # Add plane at origin location, scaled to size
            bpy.ops.mesh.primitive_plane_add(size=2, location=(width/2 + origin_x, origin_y - height/2, 0), enter_editmode=False)
            obj = bpy.context.active_object
            obj.scale.x = width / 2
            obj.scale.y = height / 2
            obj.rotation_euler.x = math.radians(90)
            opaque_objs.append(obj)

            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

            obj.name = f"b_{sprite_folder}_g{group_idx:03d}_f{frame_idx:03d}"

            # Set the parent to switch_node
            obj.parent = switch_node
            anim_states = anim_states + 1

            # Create material using texture from sprite_folder/GROUP_IDX/FRAME_IDX.png
            texture_path = f"{full_path}/{group_idx:03d}_{frame_idx:03d}.png"
            try:
                image = bpy.data.images.load(texture_path)
                mat = bpy.data.materials.new(name=f"sprite_mat_g{group_idx:03d}_f{frame_idx:03d}")
                mat.use_nodes = True
                nodes = mat.node_tree.nodes
                bsdf = nodes.get("Principled BSDF")
                if bsdf:
                    tex_node = nodes.new('ShaderNodeTexImage')
                    tex_node.image = image
                    mat.node_tree.links.new(bsdf.inputs["Base Color"], tex_node.outputs["Color"])
                obj.data.materials.append(mat)
            except RuntimeError:
                print(f"No texture found at {texture_path}")

    # convert materials
    bpy.ops.object.convert_bsdf()

    # create alpha versions
    for opaque_obj in opaque_objs:
        # duplicate opaque_obj
        bpy.ops.object.select_all(action='DESELECT')
        opaque_obj.select_set(True)
        bpy.context.view_layer.objects.active = opaque_obj
        bpy.ops.object.duplicate()

        # rename
        obj = bpy.context.active_object
        obj.name = 'c' + opaque_obj.name[1:]

        # unlink obj's materials from opaque_obj
        # Copy materials to new instances
        for i, slot in enumerate(obj.material_slots):
            original_mat = slot.material
            if original_mat:
                set_fast64_material_spr_opaque(original_mat)
                new_mat = original_mat.copy()
                set_fast64_material_spr_alpha(new_mat)
                slot.material = new_mat

        anim_states = anim_states + 1    # create alpha versions

    # create cutout versions
    for opaque_obj in opaque_objs:
        # duplicate opaque_obj
        bpy.ops.object.select_all(action='DESELECT')
        opaque_obj.select_set(True)
        bpy.context.view_layer.objects.active = opaque_obj
        bpy.ops.object.duplicate()

        # rename
        obj = bpy.context.active_object
        obj.name = 'd' + opaque_obj.name[1:]

        # unlink obj's materials from opaque_obj
        # Copy materials to new instances
        for i, slot in enumerate(obj.material_slots):
            original_mat = slot.material
            if original_mat:
                new_mat = original_mat.copy()
                set_fast64_material_spr_cutout(new_mat)
                slot.material = new_mat

        anim_states = anim_states + 1

    switch_node.switchParam = anim_states

    # Select sprite_root object in object mode
    bpy.ops.object.select_all(action='DESELECT')
    sprite_root.select_set(True)
    bpy.context.view_layer.objects.active = sprite_root
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    bpy.data.scenes["Scene"].geoTexDir = f'actors/{sprite_root.name}'
    bpy.data.scenes["Scene"].geoCustomExport = True
    bpy.data.scenes["Scene"].geoExportPath = actors_folder
    bpy.data.scenes["Scene"].geoName = f'{sprite_root.name}'
    bpy.data.scenes["Scene"].geoStructName = f'{sprite_root.name}_geo'
    bpy.ops.object.sm64_export_geolayout_object()

def stage_convert_sprs(folder, scalar):
    scalar = 1 / -scalar

    convert_mdls.wipe_scene()

    bpy.data.scenes["Scene"].bsdf_conv_all = True

    # get / create folders
    src_sprites_folder = os.path.join(folder, "sprites")
    mod_folder = os.path.join(folder, "mod")
    actors_folder = os.path.join(mod_folder, "actors")
    os.makedirs(actors_folder, exist_ok=True)

    # Loop through every folder within src_sprites_folder and call convert_spr()
    if os.path.exists(src_sprites_folder):
        for sprite_folder in os.listdir(src_sprites_folder):
            sprite_path = os.path.join(src_sprites_folder, sprite_folder)
            if os.path.isdir(sprite_path):
                convert_spr(src_sprites_folder, sprite_folder, actors_folder, scalar)
    else:
        print("Warning: sprites folder not found, skipping sprite conversion.")

    # Save to new file
    bpy.ops.wm.save_mainfile(filepath=os.path.join(folder, f"z-convert-sprs.blend"))

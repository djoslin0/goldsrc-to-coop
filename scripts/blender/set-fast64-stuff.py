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
]

def set_fast64_stuff():
    bpy.data.scenes["Scene"].f3d_simple = False

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

    # Loop through every object in the scene
    for obj in bpy.data.objects:
        # Only check objects that have material slots
        if not hasattr(obj, "material_slots"):
            continue

        # replace sky textures
        for slot in obj.material_slots:
            mat = slot.material
            if mat and (mat.name == "sky_f3d" or mat.name.startswith("sky_LM")):
                mat.f3d_mat.draw_layer.sm64 = '4'
                mat.f3d_mat.combiner1.D_alpha = '0'

                # Update the material's cache using context override
                override = bpy.context.copy()
                override['material'] = mat
                with bpy.context.temp_override(**override):
                    bpy.ops.material.update_f3d_nodes()

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
            new_mat = slot.material.copy()
            obj.material_slots[i].material = new_mat

            update = False

            if entity_rendermode == 1:
                # TODO: additive
                new_mat.f3d_mat.draw_layer.sm64 = '5'
                new_mat.f3d_mat.combiner1.A = 'PRIMITIVE'
                new_mat.f3d_mat.combiner1.C = 'TEXEL0'
                new_mat.f3d_mat.combiner1.D_alpha = 'PRIMITIVE'
                new_mat.f3d_mat.prim_color = (entity_rendercolor[0]/255, entity_rendercolor[1]/255, entity_rendercolor[2]/255, entity_renderamt/255)
                update = True

            elif entity_rendermode == 2 or entity_rendermode == 3 or entity_rendermode == 5:
                # TODO: rendermode 5 is additive
                new_mat.f3d_mat.draw_layer.sm64 = '5'
                new_mat.f3d_mat.combiner1.A = '0'
                new_mat.f3d_mat.combiner1.B = '0'
                new_mat.f3d_mat.combiner1.C = '0'
                new_mat.f3d_mat.combiner1.D = 'TEXEL0'
                new_mat.f3d_mat.combiner1.D_alpha = 'PRIMITIVE'
                new_mat.f3d_mat.prim_color = (1.0, 1.0, 1.0, entity_renderamt/255)
                update = True

            elif entity_rendermode == 4:
                new_mat.f3d_mat.draw_layer.sm64 = '4'
                new_mat.f3d_mat.combiner1.D_alpha = 'TEXEL0'
                update = True

            if update:
                update = False
                # Update the material's cache using context override
                override = bpy.context.copy()
                override['material'] = new_mat
                with bpy.context.temp_override(**override):
                    bpy.ops.material.update_f3d_nodes()

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
        print("Usage: blender --background --python set-fast64-stuff.py -- BLEND_FILE")
        sys.exit(1)

    blend_file_path = argv[0]
    if not os.path.isfile(blend_file_path):
        print(f"Error: .blend file does not exist: {blend_file_path}")
        sys.exit(1)

    # Open the .blend file
    bpy.ops.wm.open_mainfile(filepath=blend_file_path)

    set_fast64_stuff()

    # -----------------------
    # Save to new file
    # -----------------------
    folder = os.path.dirname(blend_file_path)
    save_path = os.path.join(folder, "6-set-fast64.blend")
    bpy.ops.wm.save_mainfile(filepath=save_path)
    print(f"Blender file saved: {save_path}")


if __name__ == "__main__":
    main()

import bpy
import json
import os
import convert_mdls
import export_level
import set_fast64_stuff

def read_skybox_name(folder):
    path = os.path.join(folder, 'bsp.json')
    if not os.path.exists(path):
        return None

    # read bsp.json
    with open(path, 'r') as f:
        bsp_json = json.loads(f.read())

    try:
        return bsp_json['entities']['0']['keyvalues']['skyname']
    except Exception as ex:
        return None

def check_skybox_exists(skybox_name, suffixes, skybox_dir):
    for suffix in suffixes:
        tga_filename = f"{skybox_name}{suffix}.tga"
        tga_path = os.path.join(skybox_dir, tga_filename)
        if not os.path.isfile(tga_path):
            return False
    return True

def convert_skybox_tga_to_png(skybox_name, suffixes, skybox_dir):
    for suffix in suffixes:
        tga_filename = f"{skybox_name}{suffix}.tga"
        tga_path = os.path.join(skybox_dir, tga_filename)
        png_filename = f"{skybox_name}{suffix}.png"
        png_path = os.path.join(skybox_dir, png_filename)

        if not os.path.isfile(png_path):
            image = bpy.data.images.load(tga_path)
            image.file_format = 'PNG'
            image.save(filepath=png_path)

def set_materials(skybox_name, suffixes, skybox_dir):
    for suffix in suffixes:
        mat_name = f"{suffix}_f3d"
        material = bpy.data.materials.get(mat_name)
        if material:
            filename = f"{skybox_name}{suffix}.png"
            image_path = os.path.join(skybox_dir, filename)
            image = bpy.data.images.load(image_path)
            material.f3d_mat.tex0.tex = image
            set_fast64_stuff.update_material_cache(material)

def export_skybox(skybox_name, skybox_obj, actors_folder):
    bpy.ops.object.select_all(action='DESELECT')
    skybox_obj.select_set(True)
    bpy.context.view_layer.objects.active = skybox_obj

    bpy.data.scenes["Scene"].geoTexDir = f'actors/{skybox_name}_skybox'
    bpy.data.scenes["Scene"].geoCustomExport = True
    bpy.data.scenes["Scene"].geoExportPath = actors_folder
    bpy.data.scenes["Scene"].geoName = f'{skybox_name}_skybox'
    bpy.data.scenes["Scene"].geoStructName = f'{skybox_name}_skybox_geo'
    bpy.ops.object.sm64_export_geolayout_object()

def stage_convert_skybox(folder, blend_skybox_path):
    # get skybox name
    skybox_name = read_skybox_name(folder)
    if not skybox_name:
        return False

    convert_mdls.wipe_scene()

    # Append objects from another .blend file
    export_level.append_blend_objects(blend_skybox_path)

    skybox_dir = os.path.join(folder, "skyboxes")
    mod_folder = os.path.join(folder, "mod")
    actors_folder = os.path.join(mod_folder, "actors")
    os.makedirs(actors_folder, exist_ok=True)

    suffixes = ['bk', 'dn', 'ft', 'lf', 'rt', 'up']
    skybox_exists = check_skybox_exists(skybox_name, suffixes, skybox_dir)

    if not skybox_exists:
        return False

    convert_skybox_tga_to_png(skybox_name, suffixes, skybox_dir)

    skybox_obj = bpy.data.objects.get("skybox")
    if not skybox_obj:
        return False

    set_materials(skybox_name, suffixes, skybox_dir)
    export_skybox(skybox_name, skybox_obj, actors_folder)

    # Save to new file
    bpy.ops.wm.save_mainfile(filepath=os.path.join(folder, f"z-convert-skybox.blend"))

    return True

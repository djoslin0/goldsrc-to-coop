import bpy
import os
import sys

####################
# material processing
####################

def process_material(mat, atlas_img):
    if not mat.use_nodes:
        return

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links

    # Find main nodes
    output = next((n for n in nodes if n.type == 'OUTPUT_MATERIAL'), None)
    bsdf = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)
    tex = next((n for n in nodes if n.type == 'TEX_IMAGE'), None)

    if not (output and bsdf and tex):
        return

    # Skip if already modified (UVMap_2 node exists)
    if any(n.type == 'UVMAP' and n.uv_map == 'UVMap_2' for n in nodes):
        print(f"Skipping {mat.name} (already modified)")
        return

    print(f"Modifying material: {mat.name}")

    # Create UV Map node for UVMap_2
    uvmap = nodes.new('ShaderNodeUVMap')
    uvmap.uv_map = "UVMap_2"
    uvmap.location = (tex.location.x - 300, tex.location.y - 300)

    # Create atlas texture node (already loaded)
    atlas_tex = nodes.new('ShaderNodeTexImage')
    atlas_tex.image = atlas_img
    atlas_tex.location = (uvmap.location.x + 200, uvmap.location.y)
    links.new(uvmap.outputs['UV'], atlas_tex.inputs['Vector'])

    # Create multiply node
    multiply = nodes.new('ShaderNodeMixRGB')
    multiply.blend_type = 'MULTIPLY'
    multiply.inputs[0].default_value = 1.0  # full mix
    multiply.location = (bsdf.location.x - 500, bsdf.location.y)

    # Connect texture → multiply
    links.new(tex.outputs['Color'], multiply.inputs['Color1'])
    links.new(atlas_tex.outputs['Color'], multiply.inputs['Color2'])

    # Create Gamma node
    gamma_node = nodes.new('ShaderNodeGamma')
    gamma_node.inputs[1].default_value = 0.625
    gamma_node.location = (bsdf.location.x - 250, bsdf.location.y)

    # Remove old Base Color input connection
    for link in list(bsdf.inputs['Base Color'].links):
        links.remove(link)

    # Connect multiply → gamma → bsdf
    links.new(multiply.outputs['Color'], gamma_node.inputs['Color'])
    links.new(gamma_node.outputs['Color'], bsdf.inputs['Base Color'])

    print(f"✅ {mat.name} updated successfully")


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
        print("Usage: blender --background --python blender-lightmap.py -- BLEND_FILE")
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
    atlas_img = bpy.data.images.get("atlas_0.png")
    if not atlas_img:
        print("❌ atlas_0.png not found in bpy.data.images — please load it first.")
        sys.exit(1)

    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        for slot in obj.material_slots:
            mat = slot.material
            if mat:
                process_material(mat, atlas_img)

    # -----------------------
    # Save to new file
    # -----------------------
    folder = os.path.dirname(blend_file_path)
    save_path = os.path.join(folder, "3-blender-lightmap.blend")
    bpy.ops.wm.save_mainfile(filepath=save_path)
    print(f"Blender file saved: {save_path}")


if __name__ == "__main__":
    main()

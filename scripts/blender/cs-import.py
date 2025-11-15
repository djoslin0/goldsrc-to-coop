import bpy

####################
# combine into uv2 #
####################

def get_mesh_signature(obj):
    """Return a simple signature for comparing mesh geometry."""
    if obj.type != 'MESH':
        return None
    mesh = obj.data
    return (len(mesh.vertices), len(mesh.polygons))

def main():
    # Collect candidate pairs first (so we don't modify bpy.data.objects mid-iteration)
    pairs = []
    for obj in bpy.data.objects:
        if obj.type != 'MESH' or '.' in obj.name:
            continue

        base_name = obj.name
        dup_name = base_name + ".001"

        if dup_name in bpy.data.objects:
            pairs.append((base_name, dup_name))

    # Process pairs
    for base_name, dup_name in pairs:
        original = bpy.data.objects.get(base_name)
        duplicate = bpy.data.objects.get(dup_name)
        if not original or not duplicate:
            continue

        # Make sure both are meshes and have same geometry
        if get_mesh_signature(original) != get_mesh_signature(duplicate):
            continue

        # Skip if duplicate has no UVs
        if not duplicate.data.uv_layers:
            print(f"{dup_name} has no UVs, skipping")
            continue

        dup_uv = duplicate.data.uv_layers.active
        if not dup_uv:
            print(f"{dup_name} has no active UV map, skipping")
            continue

        # Create a second UV map if it doesn't exist yet
        uv_layers = original.data.uv_layers
        new_uv = uv_layers.new(name="UVMap_2")
        print(f"Created UVMap_2 on {base_name}")

        # Copy UV coordinates
        src_uv_layer = dup_uv.data
        dst_uv_layer = new_uv.data
        if len(src_uv_layer) == len(dst_uv_layer):
            for i in range(len(src_uv_layer)):
                dst_uv_layer[i].uv = src_uv_layer[i].uv
            print(f"Copied UVs from {dup_name} → {base_name}")
        else:
            print(f"UV data mismatch between {base_name} and {dup_name}, skipping")
            continue

        # Remove the duplicate safely
        bpy.data.objects.remove(duplicate, do_unlink=True)
        print(f"Deleted {dup_name}")

# Run
main()

############
# material #
############
import bpy

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

def main2():
    # Get the preloaded atlas image
    atlas_img = bpy.data.images.get("atlas_0.png")
    if not atlas_img:
        print("❌ atlas_0.png not found in bpy.data.images — please load it first.")
        return

    for obj in bpy.data.objects:
        if obj.type != 'MESH':
            continue
        for slot in obj.material_slots:
            mat = slot.material
            if mat:
                process_material(mat, atlas_img)

main2()

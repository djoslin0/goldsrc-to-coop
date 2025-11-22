import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import import_all_objs
import combine_into_uv2
import coop_lightmap
import set_fast64_stuff
import export_level

def main():
    # Parse command-line arguments
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    if len(argv) < 3:
        print("Usage: blender --background --python goldsrc_pipeline.py -- FOLDER_PATH LEVEL_NAME APPEND_BLEND SCALAR")
        sys.exit(1)

    folder_path = argv[0]
    level_name = argv[1]
    append_file_path = argv[2]

    try:
        scalar = float(argv[3])
    except ValueError:
        print("Error: SCALAR must be a float")
        sys.exit(1)

    if not os.path.isdir(folder_path):
        print(f"Error: folder does not exist: {folder_path}")
        sys.exit(1)

    # perform this stage
    import_all_objs.stage_import_all_objs(1, folder_path, scalar)
    combine_into_uv2.stage_combine_uv2(2, folder_path)
    coop_lightmap.stage_coop_lightmap(3, folder_path)
    set_fast64_stuff.stage_set_fast64_stuff(4, folder_path)
    export_level.stage_export_level(5, folder_path, level_name, append_file_path)

if __name__ == "__main__":
    main()

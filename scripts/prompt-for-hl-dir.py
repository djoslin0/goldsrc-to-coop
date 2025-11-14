import os
import configparser
import sys

default_hl_dir = r"C:/Program Files (x86)/Steam/steamapps/common/Half-Life/"

def get_hl_dir_from_ini_configparser(ini_path):
    config = configparser.ConfigParser()
    config.optionxform = str

    config.read(ini_path, encoding="utf-8")
    if "RES" not in config:
        return default_hl_dir

    for key in ("1", "2", "3", "4"):
        if key in config["RES"]:
            path = config["RES"][key].split("?", 1)[1]
            hl_dir = os.path.dirname(path.rstrip("\\/"))
            if len(hl_dir.strip()) > 0:
                return hl_dir

    return default_hl_dir

def rewrite_res_section(ini_path, hl_dir):
    config = configparser.ConfigParser(strict=False)
    config.optionxform = str   # preserve case

    config.read(ini_path, encoding="utf-8")

    valve_path = os.path.join(hl_dir, "valve") + os.sep
    cstrike_path = os.path.join(hl_dir, "cstrike") + os.sep

    # Completely rewrite the RES section
    config["RES"] = {
        "count": "4",
        "1": "enabled?moddir/",
        "2": "enabled?moddir_addon/",
        "3": f"enabled?{valve_path}",
        "4": f"enabled?{cstrike_path}",
    }

    with open(ini_path, "w", encoding="utf-8") as f:
        config.write(f)

def check_directory(dir):
    # Required WADs relative to HL directory
    required_files = [
        os.path.join(dir, "valve", "halflife.wad")
        #os.path.join(dir, "cstrike", "cstrike.wad")
    ]
    return [f for f in required_files if not os.path.isfile(f)]

def get_valid_hl_dir(hl_dir):
    if hl_dir and len(check_directory(hl_dir)) == 0:
        return hl_dir

    while True:
        print("Enter your Half-Life directory, for example:")
        print(default_hl_dir)
        hl_dir = input("Half-Life directory: ").strip()

        # Normalize path
        hl_dir = os.path.abspath(os.path.expanduser(hl_dir))

        missing = check_directory(hl_dir)

        if missing:
            print("\n❌ ERROR: The following required WAD files were not found:\n")
            for m in missing:
                print("   " + m)
            print("\nPlease try again.\n")
            continue  # reprompt
        else:
            print("\n✅ All required WAD files found!")
            print("Half-Life directory is valid.\n")
            return hl_dir

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <path_to_bspguy.ini>")
        sys.exit(1)

    ini_path = sys.argv[1]
    if not os.path.isfile(ini_path):
        print(f"ERROR: INI file not found: {ini_path}")
        sys.exit(1)

    hl_dir = get_hl_dir_from_ini_configparser(ini_path)
    hl_dir = get_valid_hl_dir(hl_dir)
    rewrite_res_section(ini_path, hl_dir)
    print(f"✅ Updated {ini_path} successfully with HL directory: {hl_dir}")

if __name__ == "__main__":
    main()

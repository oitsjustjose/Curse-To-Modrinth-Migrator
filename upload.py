"""EH"""
import os
import json
import requests


MOD_OUTPUT_PATH = "./out/MODID"  # CHANGE ME
MODRINTH_PROJECT_ID = ""  # CHANGE ME


def main(api_key: str) -> None:
    """EH"""
    for fpath in os.listdir(MOD_OUTPUT_PATH):
        with open(f"{MOD_OUTPUT_PATH}/{fpath}", "rb") as modfile:
            data = modfile.read()

        parts = fpath.split("-")
        if len(parts) != 3:
            continue

        version_title = " ".join(parts).replace(".jar", "")
        # .x versions somehow were only ever for the .0, .1 and .2 game vers lol
        if "x" in parts[1].lower():
            root = parts[1].replace(".x", "").replace(".X", "")
            game_versions = [root, f"{root}.1", f"{root}.2"]
        else:
            game_versions = [parts[1]]
        version = parts[2].replace(".jar", "")

        payload = json.dumps(
            {
                "name": version_title,
                "version_number": f"{parts[1]}-{version}",
                "changelog": "Migrated Automagically from CurseForge",
                "dependencies": [],
                "game_versions": game_versions,
                "loaders": ["forge"],
                "featured": False,
                "requested_status": "listed",
                "version_type": "release",
                "project_id": MODRINTH_PROJECT_ID,
                "primary_file": fpath,
                "file_parts": [fpath],
            }
        )

        response = requests.post(
            "https://api.modrinth.com/v2/version",
            headers={"Authorization": api_key},
            files=[
                ("data", (None, payload, None)),
                ("files", (fpath, data, "application/octet-stream")),
            ],
        )

        if response.status_code == 200:
            print(f"Successfully uploaded {fpath} - deleting")
            os.unlink(f"{MOD_OUTPUT_PATH}/{fpath}")
        else:
            print(f"---------{fpath}---------")
            print(response.text)
            print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    if "github_token" in os.environ:
        main(os.environ["github_token"])
    else:
        print("`github_token` is not part of your PATH, add it and run again")

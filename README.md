# Curse to Modrinth Migrator

This project only handles copying files from Curse to Modrinth - nothing else. It's pretty crude but great if you want to catch up your Modrinth mod with CurseForge's versions.

## Steps

1. Install Python 3.10 from [here](https://www.python.org/downloads/release/python-3100) - scroll down to files
2. Run `pip[3][.exe] install -r requirements.txt`
3. Open `download.py`, scroll all the way to the bottom and insert a `mod_archive_all` for each mod's slug you want to automatically fully archive. One has been included by default, but you can repeat `mod_archive_all("YOURMODSLUG")` as many times as you wish. This process takes a while.
4. Run `python[3][.exe] download.py`
5. For each mod you just downloaded, modify `upload.py` at the very top to include your newly created Modrinth project ID, and the folder with all files for the mod you just downloaded from Curseforge in step 4.
6. Run `python[3][.exe] upload.py`

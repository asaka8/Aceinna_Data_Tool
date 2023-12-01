import os
import shutil

my_dirs = []

def delete_pycache_folders(directory):
    for root, dirs, files in os.walk(directory):
        for dir in dirs:
            my_dirs.append(f"{root}\\{dir}")

    for mdir in my_dirs:
        for root, dirs, files in os.walk(mdir):
            for dir in dirs:
                if dir == "__pycache__":
                    folder_path = os.path.join(root, dir)
                    shutil.rmtree(folder_path)
                    print(f"Deleted folder: {folder_path}")
            

delete_pycache_folders(".\\src")

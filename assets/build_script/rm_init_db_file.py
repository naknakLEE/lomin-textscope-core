import os

from pathlib import Path
from hydra import initialize_config_dir, compose
from pathlib import Path, PurePath
from os import environ

config_dir=environ.get(
    "CONFIG_DIR",
    PurePath("/", "workspace", "app", "assets", "conf").as_posix()
    )

initialize_config_dir(
    config_dir=config_dir)
cfg = compose(config_name="config")

permitted_file = cfg.database.insert_initial_filename

assets_path = os.path.dirname(config_dir)
dir_path = os.path.join(assets_path, "database")
dir_list = os.listdir(dir_path)

for file in dir_list:
    file_remove_extension = file.split(".")[0]
    if file_remove_extension not in permitted_file:
        print(f"[Warning] 불필요한 DB file {file} 을 삭제 합니다.")
        os.remove(os.path.join(dir_path, file))
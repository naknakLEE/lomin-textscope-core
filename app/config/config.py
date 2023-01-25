from app.common.const import get_settings

from os import environ
from pathlib import Path, PurePath
from hydra import initialize_config_dir, compose


settings = get_settings()

initialize_config_dir(config_dir=environ.get(
    "CONFIG_DIR",
    PurePath("/", "workspace", "app", "assets", "conf").as_posix()
    )
) 
hydra_cfg = compose(config_name='config')

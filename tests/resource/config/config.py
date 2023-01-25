

from os import environ
from pathlib import PurePath
from hydra import initialize_config_dir, compose


initialize_config_dir(
    config_dir=environ.get(
    "CONFIG_DIR",
    PurePath("/", "workspace", "nak2210", "tests", "resource", "conf").as_posix()
    ),
    version_base="1.1"
) 
hydra_cfg = compose(config_name='config')
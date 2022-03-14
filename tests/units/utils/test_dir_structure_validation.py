import pytest
from typing import Callable
from tempfile import TemporaryDirectory
from pathlib import Path
from app.utils.utils import dir_structure_validation


@pytest.mark.unit
class TestDirStructureValidation:
    tmp_path: TemporaryDirectory
    root_path: Path

    def setup_method(self, method: Callable) -> None:
        self.tmp_path = TemporaryDirectory()
        self.root_path = Path(self.tmp_path.name)

    def teardown_method(self, method: Callable) -> None:
        self.tmp_path.cleanup()

    def generate_fake_dirs(
        self,
        exist_file_under_root_dir: bool = False,
        empty_root_dirs: bool = False,
        exist_sub_dir: bool = False,
        empty_sub_dir: bool = False,
        exist_unsupporeted_ext: bool = False,
    ) -> None:
        dummy_root_path = self.root_path
        if exist_file_under_root_dir:
            file_name = f"under_the_root.txt"
            with open(self.root_path.joinpath(file_name), "w") as file_io:
                file_io.write("test")
        if not empty_root_dirs:
            dir_name = "category_1"
            dummy_root_path = Path(dummy_root_path, dir_name)
            dummy_root_path.mkdir(exist_ok=True)
            if exist_sub_dir:
                dir_name = "sub_dir"
                Path(dummy_root_path, dir_name).mkdir(exist_ok=True, parents=True)
            if not empty_sub_dir:
                file_name = "image"
                if exist_unsupporeted_ext:
                    file_name += ".another"
                else:
                    file_name += ".jpg"
                with open(Path(dummy_root_path, file_name), "w") as file_io:
                    file_io.write("test")

    def test_root_dir_is_empty(self) -> None:
        self.generate_fake_dirs(empty_root_dirs=True)
        with pytest.raises(ValueError):
            dir_structure_validation(self.root_path)

    def test_exist_file_under_the_root_dir(self) -> None:
        self.generate_fake_dirs(exist_file_under_root_dir=True)
        with pytest.raises(ValueError):
            dir_structure_validation(self.root_path)

    def test_category_dir_is_empty(self) -> None:
        self.generate_fake_dirs(empty_sub_dir=True)
        with pytest.raises(ValueError):
            dir_structure_validation(self.root_path)

    def test_category_dir_include_sub_dir(self) -> None:
        self.generate_fake_dirs(exist_sub_dir=True)
        with pytest.raises(ValueError):
            dir_structure_validation(self.root_path)

    def test_include_unsupported_extension_file(self) -> None:
        self.generate_fake_dirs(exist_unsupporeted_ext=True)
        with pytest.raises(ValueError):
            dir_structure_validation(self.root_path)

    def test_normal_case(self) -> None:
        self.generate_fake_dirs()
        output = dir_structure_validation(self.root_path)
        assert output == True

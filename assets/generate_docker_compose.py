import yaml  # type: ignore
import argparse
import typing as t
from pathlib import Path


class DeployService:
    def __init__(
        self,
        base_path: str,
        yaml: t.List,
        save_path: str,
        serving_image: str,
        web_image: str,
        pp_image: str,
        wrapper_image: str,
        deploy_services: t.List,
    ):
        self.config_path = Path(base_path).resolve()
        self.save_path = Path(save_path).resolve()
        self.yaml_files = yaml
        self.config = self.load_yaml()
        self.config_version = None
        self.deploy_services = deploy_services
        self.image_name_dict = {
            "serving": serving_image,
            "web": web_image,
            "pp": pp_image,
            "wrapper": wrapper_image,
        }

    def load_yaml(self):
        config = {}
        for yaml_file in self.yaml_files:
            with self.config_path.joinpath(yaml_file).open("r") as file_io:
                config.update({yaml_file: yaml.load(file_io, Loader=yaml.FullLoader)})
        return config

    def parse(self):
        for yaml_file in self.yaml_files:
            config = self.config.get(yaml_file)
            services = {
                service: service_conf
                for service, service_conf in config["services"].items()
                if service in self.deploy_services
            }
            for service, service_conf in services.items():
                if "build" in service_conf:
                    del service_conf["build"]
                if yaml_file.endswith(".prod.yml"):
                    if service == "wrapper":
                        service_conf["volumes"] = [
                            service_conf["volumes"][0].replace("./", "./wrapper/")
                        ]
                    image_name = self.image_name_dict.get(service, None)
                    if image_name is None:
                        continue
                    service_conf["image"] = image_name
                    services[service].update(service_conf)
                services.update({service: service_conf})
            config.update({"services": services})
            self.config[yaml_file].update(config)

    def save_yaml(self):
        for yaml_file in self.yaml_files:
            with self.save_path.joinpath(yaml_file).open("w") as file_io:
                yaml.dump(self.config[yaml_file], file_io, sort_keys=True, indent=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--base-path",
        action="store",
        default=".",
        help="Input base path which include assets (default: .)",
    )
    parser.add_argument(
        "--yaml",
        nargs="+",
        default=["docker-compose.yml", "docker-compose.prod.yml"],
        help="Input file name to load docker compose (default: ['docker-compose.yml', 'docker-compose.prod.yml'])",
    )
    parser.add_argument(
        "--save-path",
        action="store",
        default="../",
        help="Input path to save for generated docker compose file (default: ../)",
    )
    parser.add_argument(
        "--serving-image",
        action="store",
        default="docker.lomin.ai/ts-gpu-serving:0.6.0",
        help="Input serving image name (default: docker.lomin.ai/ts-gpu-serving:0.6.0)",
    )
    parser.add_argument(
        "--web-image",
        action="store",
        default="docker.lomin.ai/ts-web:0.6.0",
        help="Input web image name (default: docker.lomin.ai/ts-web:0.6.0)",
    )
    parser.add_argument(
        "--pp-image",
        action="store",
        default="docker.lomin.ai/ts-pp:0.6.0",
        help="Input pp image name (default: docker.lomin.ai/ts-pp:0.6.0)",
    )
    parser.add_argument(
        "--wrapper-image",
        action="store",
        default="docker.lomin.ai/ts-wrapper:0.6.0",
        help="Input wrapper image name (default: docker.lomin.ai/ts-wrapper:0.6.0)",
    )
    parser.add_argument(
        "--deploy-services",
        nargs="+",
        default=[
            "web",
            "wrapper",
            "serving",
            "pp",
            "minio",
            "elasticsearch",
            "kibana",
            "openldap",
            "pgadmin",
            "postgres",
        ],
        help="Add deploy service name (default: ['web', 'wrapper', 'serving', 'pp', 'minio', 'elasticsearch', 'kibana', 'openldap', 'pgadmin', 'postgres'])",
    )

    args = parser.parse_args()
    deploy_service = DeployService(**vars(args))
    deploy_service.parse()
    deploy_service.save_yaml()

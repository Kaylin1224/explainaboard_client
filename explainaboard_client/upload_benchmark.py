import argparse
import json
import time
import os
from explainaboard_api_client.model.system import System
from explainaboard_api_client.model.system_create_props import SystemCreateProps
from explainaboard_api_client.model.system_metadata import SystemMetadata
from explainaboard_api_client.model.system_output_props import SystemOutputProps
from explainaboard_client import Config, ExplainaboardClient
from explainaboard_client.tasks import (
    DEFAULT_METRICS,
    FileType,
    infer_file_type,
    TaskType,
)
from explainaboard_client.utils import generate_dataset_id


def validate_outputs(system_outputs):
    for pth in system_outputs:
        if not os.path.basename(pth).split(".")[0].split("_")[0].isdigit():
            raise ValueError(
                f"system output file name: {pth}  should"
                f" start with number,"
                "for example: 8.json"
            )
    return True


def main():

    # Parse arguments
    parser = argparse.ArgumentParser(
        description="A command-line tool to upload benchmark "
        "to the ExplainaBoard web interface."
    )
    parser.add_argument(
        "--email",
        type=str,
        required=True,
        help="Email address used to sign in to ExplainaBoard",
    )
    parser.add_argument("--api_key", type=str, required=True, help="Your API key")

    parser.add_argument(
        "--public", action="store_true", help="Make the uploaded system public"
    )

    parser.add_argument("--system_name", type=str, help="system_name")

    parser.add_argument("--benchmark", type=str, help="benchmark config")

    parser.add_argument(
        "--system_outputs", type=str, nargs="+", help="benchmark config"
    )

    parser.add_argument(
        "--system_details", type=str, help="File of system details in JSON format"
    )

    parser.add_argument(
        "--shared_users", type=str, nargs="+", help="Emails of users to share with"
    )
    parser.add_argument(
        "--server",
        type=str,
        required=False,
        default="main",
        choices=["main", "staging", "local"],
        help='Which server to upload to, "main" should be sufficient',
    )
    args = parser.parse_args()

    benchmark = args.benchmark
    with open(benchmark, "r") as f:
        benchmark_config = json.load(f)

    system_outputs = args.system_outputs

    if validate_outputs(system_outputs):
        system_outputs.sort(
            key=lambda system_path: int(
                os.path.basename(system_path).split(".")[0].split("_")[0]
            )
        )
    else:
        raise ValueError("System output file names should start with number")

    shared_users = args.shared_users or []
    # Read system details file
    system_details = {}
    if args.system_details:
        with open(args.system_details, "r") as fin:
            system_details = json.load(fin)

    for idx, dataset_info in enumerate(benchmark_config["datasets"]):
        if idx > 0:
            time.sleep(5)
        dataset_name = dataset_info["dataset_name"]
        sub_dataset = dataset_info["sub_dataset"]
        dataset_split = dataset_info["dataset_split"]
        metric_names = [metric_dict["name"] for metric_dict in dataset_info["metrics"]]
        task = dataset_info["task"]
        source_language = "en"  # this should be obtained from benchmark config
        target_language = "en"  # this should be obtained from benchmark config
        output_file_type = dataset_info["output_file_type"]

        # Do the actual upload
        system_output = SystemOutputProps(
            data=system_outputs[idx],
            file_type=output_file_type,
        )

        metadata = SystemMetadata(
            task=task,
            is_private=not args.public,
            system_name=args.system_name,
            metric_names=metric_names,
            source_language=source_language,
            target_language=target_language,
            dataset_metadata_id=generate_dataset_id(dataset_name, sub_dataset),
            dataset_split=dataset_split,
            shared_users=shared_users,
            system_details=system_details,
        )

        create_props = SystemCreateProps(
            metadata=metadata, system_output=system_output, custom_datset=None
        )
        client_config = Config(
            args.email,
            args.api_key,
            args.server,
        )
        client = ExplainaboardClient(client_config)

        result: System = client.systems_post(create_props)
        try:
            sys_id = result.system_id
            client.systems_system_id_get(sys_id)
            print(f"successfully posted system {args.system_name} with ID {sys_id}")
        except Exception:
            print(f"failed to post system {args.system_name}")
            pass


if __name__ == "__main__":
    main()

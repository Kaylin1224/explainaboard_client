import argparse
import json
import traceback

import explainaboard_client
from explainaboard_client import ExplainaboardClient
from explainaboard_client.config import get_frontend
from explainaboard_client.tasks import FileType, TaskType


def main():

    # Parse arguments
    parser = argparse.ArgumentParser(
        description="A command-line tool to evaluate system "
        "to the ExplainaBoard web interface."
    )
    # ---- Authentication arguments
    parser.add_argument(
        "--username",
        type=str,
        default=explainaboard_client.username,
        help="Username used to sign in to ExplainaBoard. Defaults to the EB_USERNAME "
        "environment variable.",
    )
    parser.add_argument(
        "--api_key",
        type=str,
        default=explainaboard_client.api_key,
        help="API key for ExplainaBoard. Defaults to the EB_API_KEY environment "
        "variable.",
    )
    # ---- System info
    parser.add_argument(
        "--task",
        type=str,
        required=True,
        choices=TaskType.list(),
        help="What task you will be analyzing",
    )
    parser.add_argument(
        "--system_name",
        type=str,
        required=True,
        help="Name of the system that you are evaluating",
    )
    parser.add_argument(
        "--system_output_file",
        type=str,
        required=True,
        help="Path to the system output file",
    )
    parser.add_argument(
        "--system_output_file_type",
        type=str,
        choices=FileType.list(),
        help="File type of the system output (eg text/json/tsv/conll)",
    )
    dataset_group = parser.add_mutually_exclusive_group(required=True)
    dataset_group.add_argument(
        "--dataset", type=str, help="A dataset name from DataLab"
    )
    parser.add_argument(
        "--sub_dataset",
        type=str,
        required=False,
        help="A sub-dataset name from DataLab",
    )
    parser.add_argument(
        "--split",
        type=str,
        required=False,
        default="test",
        help="The name of the dataset split to process",
    )
    dataset_group.add_argument(
        "--custom_dataset_file", type=str, help="The path to a custom dataset file"
    )
    parser.add_argument(
        "--custom_dataset_file_type",
        type=str,
        required=False,
        choices=FileType.list(),
        help="File type of the custom dataset (eg text/json/tsv/conll)",
    )
    parser.add_argument(
        "--metric_names",
        type=str,
        nargs="+",
        required=False,
        help="The metrics to compute, leave blank for task defaults",
    )
    parser.add_argument(
        "--source_language", type=str, help="The language on the input side"
    )
    parser.add_argument(
        "--target_language", type=str, help="The language on the output side"
    )
    parser.add_argument(
        "--system_details_file", type=str, help="File of system details in JSON format"
    )
    parser.add_argument(
        "--public", action="store_true", help="Make the evaluation results public"
    )
    parser.add_argument(
        "--shared_users", type=str, nargs="+", help="Emails of users to share with"
    )
    parser.add_argument(
        "--report_file",
        type=str,
        help="A path to a file where the JSON report will be written",
    )
    args = parser.parse_args()

    explainaboard_client.username = args.username
    explainaboard_client.api_key = args.api_key
    client = ExplainaboardClient()

    try:
        evaluation_data = client.evaluate_system_file(
            task=args.task,
            system_name=args.system_name,
            system_output_file=args.system_output_file,
            system_output_file_type=args.system_output_file_type,
            dataset=args.dataset,
            sub_dataset=args.sub_dataset,
            split=args.split,
            custom_dataset_file=args.custom_dataset_file,
            custom_dataset_file_type=args.custom_dataset_file_type,
            metric_names=args.metric_names,
            source_language=args.source_language,
            target_language=args.target_language,
            system_details_file=args.system_details_file,
            public=args.public,
            shared_users=args.shared_users,
        )
        frontend = get_frontend(explainaboard_client.environment)
        sys_id = evaluation_data["system_id"]
        if args.report_file is not None:
            with open(args.report_file, "w") as fout:
                json.dump(evaluation_data, fout, default=str)
        print(f"Successfully evaluated system {args.system_name} with ID {sys_id}")
        print(f"View it at {frontend}/systems?system_id={sys_id}")
    except Exception:
        evaluation_data = None
        print(f"failed to evaluate system {args.system_name}")
        traceback.print_exc()

    # Print accuracy numbers
    if evaluation_data is not None:
        try:
            overall_results = evaluation_data["system_info"]["results"]["overall"][0]
            for result in overall_results:
                print(
                    f'{result["metric_name"]}: {result["value"]:.4f} '
                    f'[{result["confidence_score_low"]:.4f}, '
                    f'{result["confidence_score_high"]:.4f}]'
                )
        except Exception:
            pass


if __name__ == "__main__":
    main()

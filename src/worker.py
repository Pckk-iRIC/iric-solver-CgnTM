import argparse
import os
import re
import shutil
import sys
import zipfile
from pathlib import Path

import h5py
import numpy as np


class MergerError(Exception):
    def __init__(self, message, exit_code=10, allow_skip=True):
        super().__init__(message)
        self.exit_code = exit_code
        self.allow_skip = allow_skip


POINTER_DATASETS = [
    "FlowSolutionPointers",
    "FlowCellSolutionPointers",
    "FlowIFaceSolutionPointers",
    "FlowJFaceSolutionPointers",
    "GridCoordinatesPointers",
]


def natural_sort_key(text):
    parts = re.split(r"(\d+)", text)
    key = []
    for part in parts:
        if part.isdigit():
            key.append(int(part))
        else:
            key.append(part.lower())
    return key


def decode_cgns_names(data):
    names = []
    for row in data:
        raw = bytes(row).split(b"\x00", 1)[0]
        names.append(raw.decode("utf-8", errors="ignore"))
    return names


def encode_cgns_names(names, width):
    data = np.zeros((len(names), width), dtype=np.int8)
    for i, name in enumerate(names):
        raw = name.encode("utf-8")
        if len(raw) >= width:
            raise MergerError(
                f"ポインタ名が長すぎます: {name} (上限 {width - 1} 文字)",
                exit_code=3,
            )
        data[i, : len(raw)] = np.frombuffer(raw, dtype=np.uint8).astype(np.int8)
    return data


def rename_with_index(name, index):
    match = re.search(r"(\d+)$", name)
    if match:
        return f"{name[:match.start()]}{index}"
    return f"{name}{index}"


def open_output_cgns(output_path, template_path):
    if not output_path.exists():
        try:
            shutil.copy(template_path, output_path)
        except OSError as exc:
            raise MergerError("出力ファイルを作成できません。", exit_code=4) from exc
    try:
        return h5py.File(output_path, "r+")
    except OSError as exc:
        raise MergerError("出力CGNSを開けません。", exit_code=4) from exc


def time_from_filename(path):
    match = re.search(r"(\d+)(?!.*\d)", path.stem)
    if not match:
        raise MergerError(
            f"ファイル名から時刻を取得できません: {path.name}",
            exit_code=3,
            allow_skip=False,
        )
    return float(match.group(1))


def resolve_project_root(project_path):
    if project_path.is_file() and project_path.suffix.lower() == ".ipro":
        return "ipro"
    if project_path.is_dir():
        if not (project_path / "project.xml").exists():
            raise MergerError("project.xml が見つかりません。", exit_code=2)
        return "folder"
    raise MergerError("入力パスが存在しません。", exit_code=2)


def prepare_output_project(project_path, output_dir):
    input_name = project_path.stem if project_path.is_file() else project_path.name
    output_project_root = output_dir / input_name
    output_ipro_path = output_dir / f"{input_name}.ipro"

    if output_project_root.exists() or output_ipro_path.exists():
        raise MergerError(
            "出力先に同名のファイルまたはフォルダが存在します。削除または出力先変更が必要です。",
            exit_code=2,
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    if project_path.is_file():
        with zipfile.ZipFile(project_path, "r") as zf:
            zf.extractall(output_project_root)
    else:
        shutil.copytree(project_path, output_project_root)

    if not (output_project_root / "project.xml").exists():
        raise MergerError("出力先に project.xml が見つかりません。", exit_code=2)

    return input_name, output_project_root, output_ipro_path


def read_pointer_templates(solution_path):
    templates = {}
    with h5py.File(solution_path, "r") as f:
        zone_iter = f.get("iRIC/iRICZone/ZoneIterativeData")
        if zone_iter is None:
            return templates
        for pointer in POINTER_DATASETS:
            if pointer not in zone_iter:
                continue
            data = zone_iter[f"{pointer}/ data"][()]
            names = decode_cgns_names(data)
            if len(names) != 1:
                raise MergerError(
                    f"{pointer} が単一エントリではありません。", exit_code=3
                )
            templates[pointer] = {
                "input_name": names[0],
                "width": data.shape[1],
            }
    return templates


def read_base_iterative_items(solution_path):
    items = []
    with h5py.File(solution_path, "r") as f:
        base_iter = f.get("iRIC/BaseIterativeData")
        if base_iter is None:
            return items
        for key in base_iter.keys():
            if key == "TimeValues":
                continue
            group = base_iter.get(key)
            if group is None:
                continue
            if " data" in group:
                items.append(key)
    return items


def read_time_value(f):
    ds = f.get("iRIC/BaseIterativeData/TimeValues/ data")
    if ds is None:
        raise MergerError(
            "TimeValues が見つかりません。", exit_code=3, allow_skip=False
        )
    values = ds[()]
    if len(values) == 0:
        raise MergerError("TimeValues が空です。", exit_code=3, allow_skip=False)
    return float(values[0])


def read_grid_shape(f):
    zone = f.get("iRIC/iRICZone")
    if zone is None:
        return None
    grid = zone.get("GridCoordinates")
    if grid is None:
        return None
    x = grid.get("CoordinateX/ data")
    y = grid.get("CoordinateY/ data")
    if x is None or y is None:
        return None
    return (x.shape, y.shape)


def build_solution_entries(
    solution_paths, time_source, missing_policy, base_items
):
    entries = []
    base_values = {name: [] for name in base_items}
    grid_shape = None

    for index, path in enumerate(solution_paths, start=1):
        try:
            with h5py.File(path, "r") as f:
                if time_source == "from_cgns":
                    time_value = read_time_value(f)
                else:
                    time_value = time_from_filename(path)

                if base_items:
                    for name in base_items:
                        ds = f.get(f"iRIC/BaseIterativeData/{name}/ data")
                        if ds is None:
                            raise MergerError(
                                f"BaseIterativeData の {name} が見つかりません。",
                                exit_code=3,
                            )
                        value = ds[()]
                        if np.size(value) == 0:
                            raise MergerError(
                                f"BaseIterativeData の {name} が空です。",
                                exit_code=3,
                            )
                        base_values[name].append(float(np.ravel(value)[0]))

                current_shape = read_grid_shape(f)
                if grid_shape is None:
                    grid_shape = current_shape
                elif current_shape is not None and current_shape != grid_shape:
                    raise MergerError("格子サイズが一致しません。", exit_code=3)

            entries.append({"path": path, "time": time_value})
        except MergerError as exc:
            if missing_policy == "skip" and exc.allow_skip:
                print(f"警告: {path.name} をスキップしました。理由: {exc}")
                continue
            raise

    return entries, base_values


def update_base_iterative_data(output_file, times, base_values):
    base_iter = output_file.require_group("iRIC/BaseIterativeData")
    time_group = base_iter.require_group("TimeValues")
    if " data" in time_group:
        del time_group[" data"]
    time_group.create_dataset(" data", data=np.array(times, dtype=np.float64))

    for name, values in base_values.items():
        group = base_iter.require_group(name)
        if " data" in group:
            del group[" data"]
        group.create_dataset(" data", data=np.array(values, dtype=np.float64))


def update_zone_pointers(output_file, pointer_outputs, pointer_widths):
    zone_iter = output_file.require_group("iRIC/iRICZone/ZoneIterativeData")
    for pointer, names in pointer_outputs.items():
        group = zone_iter.require_group(pointer)
        if " data" in group:
            del group[" data"]
        width = pointer_widths[pointer]
        group.create_dataset(" data", data=encode_cgns_names(names, width))


def copy_solution_groups(output_file, entries, pointer_templates):
    zone = output_file.require_group("iRIC/iRICZone")

    pointer_outputs = {}
    pointer_widths = {}
    for pointer, template in pointer_templates.items():
        input_name = template["input_name"]
        width = template["width"]
        pointer_widths[pointer] = width
        pointer_outputs[pointer] = [
            rename_with_index(input_name, i + 1) for i in range(len(entries))
        ]

        for name in pointer_outputs[pointer]:
            if name in zone:
                del zone[name]

    for index, entry in enumerate(entries, start=1):
        with h5py.File(entry["path"], "r") as src:
            src_zone = src.get("iRIC/iRICZone")
            if src_zone is None:
                raise MergerError("iRICZone が見つかりません。", exit_code=3)

            for pointer, template in pointer_templates.items():
                input_name = template["input_name"]
                output_name = rename_with_index(input_name, index)
                if input_name not in src_zone:
                    raise MergerError(
                        f"{input_name} が {entry['path'].name} に見つかりません。",
                        exit_code=3,
                    )
                zone.copy(src_zone[input_name], output_name)

    update_zone_pointers(output_file, pointer_outputs, pointer_widths)


def merge_project(
    project_path,
    output_dir,
    result_dir,
    pattern,
    time_source,
    missing_policy,
    dry_run,
    output_cgns_name,
):
    if not output_cgns_name:
        output_cgns_name = "Case1.cgn"

    project_type = resolve_project_root(project_path)
    input_name, output_root, output_ipro = prepare_output_project(
        project_path, output_dir
    )

    result_path = output_root / result_dir
    if not result_path.exists():
        raise MergerError("分割CGNSの格納フォルダが見つかりません。", exit_code=2)

    solution_paths = sorted(result_path.glob(pattern), key=lambda p: natural_sort_key(p.name))
    if not solution_paths:
        raise MergerError("対象CGNSが見つかりません。", exit_code=2)

    print(f"対象ファイル数: {len(solution_paths)}")
    print(f"出力プロジェクト: {output_root}")

    pointer_templates = read_pointer_templates(solution_paths[0])
    if not pointer_templates:
        raise MergerError("ポインタ情報が見つかりません。", exit_code=3)

    base_items = read_base_iterative_items(solution_paths[0])
    entries, base_values = build_solution_entries(
        solution_paths, time_source, missing_policy, base_items
    )

    if not entries:
        raise MergerError("有効なCGNSがありません。", exit_code=2)

    if dry_run:
        print("dry-runのため出力を作成しません。")
        shutil.rmtree(output_root)
        return project_type, None, None, True

    base_cgns = output_root / output_cgns_name
    with open_output_cgns(base_cgns, entries[0]["path"]) as out_f:
        copy_solution_groups(out_f, entries, pointer_templates)
        update_base_iterative_data(out_f, [e["time"] for e in entries], base_values)

    result_output_dir = output_root / result_dir
    if result_output_dir.exists():
        shutil.rmtree(result_output_dir)

    if project_type == "ipro":
        with zipfile.ZipFile(output_ipro, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(output_root):
                for file_name in files:
                    full_path = Path(root) / file_name
                    rel_path = full_path.relative_to(output_root)
                    zf.write(full_path, rel_path.as_posix())
        shutil.rmtree(output_root)

    return project_type, output_root, output_ipro, False


def merge_result_dir(
    result_dir,
    output_dir,
    pattern,
    time_source,
    missing_policy,
    dry_run,
    output_cgns_name,
):
    if not output_cgns_name:
        output_cgns_name = "Case1.cgn"

    result_path = result_dir
    if not result_path.exists():
        raise MergerError("分割CGNSの格納フォルダが見つかりません。", exit_code=2)
    if not result_path.is_dir():
        raise MergerError("分割CGNSの格納フォルダがディレクトリではありません。", exit_code=2)

    solution_paths = sorted(
        result_path.glob(pattern), key=lambda p: natural_sort_key(p.name)
    )
    if not solution_paths:
        raise MergerError("対象CGNSが見つかりません。", exit_code=2)

    print(f"対象ファイル数: {len(solution_paths)}")
    print(f"入力resultフォルダ: {result_path}")

    pointer_templates = read_pointer_templates(solution_paths[0])
    if not pointer_templates:
        raise MergerError("ポインタ情報が見つかりません。", exit_code=3)

    base_items = read_base_iterative_items(solution_paths[0])
    entries, base_values = build_solution_entries(
        solution_paths, time_source, missing_policy, base_items
    )

    if not entries:
        raise MergerError("有効なCGNSがありません。", exit_code=2)

    if dry_run:
        print("dry-runのため出力を作成しません。")
        return None, True

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_cgns_name

    with open_output_cgns(output_path, entries[0]["path"]) as out_f:
        copy_solution_groups(out_f, entries, pointer_templates)
        update_base_iterative_data(out_f, [e["time"] for e in entries], base_values)

    return output_path, False


def build_parser():
    parser = argparse.ArgumentParser(
        description="iRICの分割CGNSを単一プロジェクトに統合します。"
    )
    parser.add_argument("--project", help="入力プロジェクト(.iproまたはフォルダ)")
    parser.add_argument(
        "--result-dir-input",
        help="分割CGNSのresultフォルダを直接指定",
    )
    parser.add_argument("--output-dir", required=True, help="出力先ディレクトリ")
    parser.add_argument(
        "--result-dir", default="result", help="分割CGNS格納フォルダ名"
    )
    parser.add_argument(
        "--pattern", default="Solution*.cgn", help="対象ファイルパターン"
    )
    parser.add_argument(
        "--output-cgns-name",
        help="出力CGNSファイル名(既定: Case1.cgn)",
    )
    parser.add_argument(
        "--time-source",
        choices=["from_filename", "from_cgns"],
        default="from_filename",
        help="時刻の取得元",
    )
    parser.add_argument(
        "--missing-policy",
        choices=["error", "skip"],
        default="error",
        help="欠損時の挙動",
    )
    parser.add_argument("--dry-run", action="store_true", help="検査のみ実行")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.project and args.result_dir_input:
        print("エラー: --project と --result-dir-input は同時に指定できません。")
        return 2
    if not args.project and not args.result_dir_input:
        print("エラー: 入力パスが指定されていません。")
        return 2

    output_dir = Path(args.output_dir).expanduser()
    output_cgns_name = args.output_cgns_name or "Case1.cgn"

    try:
        if args.project:
            project_path = Path(args.project).expanduser()
            project_type, output_root, output_ipro, dry_run = merge_project(
                project_path=project_path,
                output_dir=output_dir,
                result_dir=args.result_dir,
                pattern=args.pattern,
                time_source=args.time_source,
                missing_policy=args.missing_policy,
                dry_run=args.dry_run,
                output_cgns_name=output_cgns_name,
            )
        else:
            result_dir = Path(args.result_dir_input).expanduser()
            output_cgns, dry_run = merge_result_dir(
                result_dir=result_dir,
                output_dir=output_dir,
                pattern=args.pattern,
                time_source=args.time_source,
                missing_policy=args.missing_policy,
                dry_run=args.dry_run,
                output_cgns_name=output_cgns_name,
            )
    except MergerError as exc:
        print(f"エラー: {exc}")
        return exc.exit_code
    except Exception as exc:
        print(f"想定外エラー: {exc}")
        return 10

    if dry_run:
        print("dry-run完了: 出力は作成していません。")
        return 0

    if args.project:
        if project_type == "ipro":
            print(f"出力完了: {output_ipro}")
        else:
            print(f"出力完了: {output_root}")
    else:
        print(f"出力完了: {output_cgns}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

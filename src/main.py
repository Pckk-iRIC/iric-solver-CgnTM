import subprocess
import sys
from pathlib import Path


def run_worker_direct(argv):
    this_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(this_dir))
    import worker

    return worker.main(argv)


def read_calc_string(iric, fid, name, default=None):
    try:
        value = iric.cg_iRIC_Read_String(fid, name)
    except Exception:
        return default
    if value is None:
        return default
    text = str(value)
    if text == "":
        return default
    return text


def read_calc_int(iric, fid, name, default=None):
    try:
        value = iric.cg_iRIC_Read_Integer(fid, name)
    except Exception:
        return default
    try:
        return int(value)
    except Exception:
        return default


def run_from_iric(cgn_path):
    solver_dir = Path(__file__).resolve().parent

    try:
        import iric
    except Exception as exc:
        print(f"エラー: iRICラッパーの読み込みに失敗しました。{exc}")
        return 2

    try:
        fid = iric.cg_iRIC_Open(str(cgn_path), iric.IRIC_MODE_READ)
    except Exception as exc:
        print(f"エラー: iRICのCGNSを開けません。{exc}")
        return 2

    input_type = read_calc_int(iric, fid, "input_type", default=0)
    if input_type == 0:
        project_path = read_calc_string(iric, fid, "calc_ipro")
        project_label = "入力ipro"
    elif input_type == 1:
        project_path = read_calc_string(iric, fid, "calc_folder")
        project_label = "入力プロジェクトフォルダ"
    elif input_type == 2:
        project_path = read_calc_string(iric, fid, "result_dir_input")
        project_label = "入力resultフォルダ"
    else:
        project_path = None
        project_label = "入力パス"

    output_dir = read_calc_string(iric, fid, "output_dir")
    output_name_mode = read_calc_int(iric, fid, "output_name_mode", default=0)
    output_cgns_name = read_calc_string(
        iric, fid, "output_cgns_name", default="Merged_Solution.cgn"
    )
    result_subdir = read_calc_string(iric, fid, "result_subdir", default="result")
    pattern = read_calc_string(iric, fid, "pattern", default="Solution*.cgn")
    time_source_value = read_calc_int(iric, fid, "time_source", default=0)
    missing_policy_value = read_calc_int(iric, fid, "missing_policy", default=0)
    dry_run_value = read_calc_int(iric, fid, "dry_run", default=0)
    iric.cg_iRIC_Close(fid)

    if input_type not in (0, 1, 2):
        print("エラー: 入力の種類が不正です。")
        return 2
    if not project_path:
        print(f"エラー: {project_label}のパスが指定されていません。")
        return 2
    if not output_dir:
        print("エラー: 出力先フォルダのパスが指定されていません。")
        return 2

    run_venv = solver_dir / "run_venv_python.bat"
    if not run_venv.exists():
        run_venv = solver_dir.parent / "run_venv_python.bat"
    if not run_venv.exists():
        print("エラー: run_venv_python.bat が見つかりません。")
        return 2

    worker_path = solver_dir / "worker.py"
    time_source = "from_cgns" if time_source_value == 1 else "from_filename"
    missing_policy = "skip" if missing_policy_value == 1 else "error"

    cmd = [
        "cmd",
        "/c",
        str(run_venv),
        str(worker_path),
        "--output-dir",
        output_dir,
        "--pattern",
        pattern,
        "--time-source",
        time_source,
        "--missing-policy",
        missing_policy,
    ]
    if input_type in (0, 1):
        cmd.extend(["--project", project_path, "--result-dir", result_subdir])
    else:
        cmd.extend(["--result-dir-input", project_path])
    if output_name_mode == 1 and output_cgns_name:
        cmd.extend(["--output-cgns-name", output_cgns_name])
    if dry_run_value == 1:
        cmd.append("--dry-run")

    result = subprocess.run(cmd, cwd=str(solver_dir))
    return result.returncode


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if "--project" in args or "--output-dir" in args:
        return run_worker_direct(args)

    if len(args) == 1:
        return run_from_iric(Path(args[0]))

    print("エラー: 引数が不正です。")
    print("例: main.py --project <path> --output-dir <path>")
    return 2


if __name__ == "__main__":
    sys.exit(main())

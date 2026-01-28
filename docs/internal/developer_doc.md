# 開発者用ドキュメント
本ドキュメントはソルバー開発者向けのドキュメントです。
本プロジェクトではPythonでの開発を前提としていますが、iRICのMinicondaをダウンロードされていればPython環境もついてくるので、特に環境構築は不要です。
**実行する際はコマンドプロンプトを利用してください。**

## 本リポジトリディレクトリ構造（ドキュメント作成時点）

```
iRICv4-CGNS-Timestep-Merger/
├── .git/
├── .gitattributes
├── .gitignore
├── AGENTS.md
├── CgnTM_v4/
│   ├── README
│   ├── definition.xml
│   ├── main.py
│   ├── run_iric_python.bat
│   ├── run_solver.bat
│   ├── run_venv_python.bat
│   └── worker.py
├── README.md
├── archive/
│   └── CgnTM-v1.0_v4.zip
├── docs/
│   ├── developer_docs.md
│   ├── iricv4_cgns_timestep_merger_agent_brief.md
│   ├── requirements.md
│   └── developper_doc.md
├── run_iric_python.bat
├── run_venv_python.bat
├── sandbox/
│   ├── cgns_tree.py
│   ├── definition.xml
│   ├── go.bat
│   ├── iric.py
│   └── output_test/
```

**注記**: .gitignoreで除外されているディレクトリとファイル：
- `data/` - テストデータ用ディレクトリ
- `*.log` - ログファイル（terminal.logを含む）
- `venv/` - Python仮想環境
- `docs/v4_jp/` - iRIC開発者マニュアル日本語ドキュメント


### 重要ディレクトリの説明
 - `CgnTM_v4/` - ソルバー本体、こちらをiRICの `private/solvers/` に配置して利用する。
 - `archive/` - 過去リリースのアーカイブ（Releasesでも管理中）


### 環境について
開発環境セットアップについては特にスクリプトを用意していないため、手動で作成する必要があります。
本リポジトリで開発する場合はiRICのPythonインタプリターを利用し、リポジトリルートへ仮想環境を作成し、そこへ依存関係をインストールする必要があります。


### 実行方法について
仮想環境が作成できたら`run_venv_python.bat`と`run_iric_python.bat`を利用する環境に合わせてパスを編集してください。
それぞれの用途についてはiRICのライブラリを使用したい場合は`run_iric_python.bat`、標準のPythonインタプリターを使用したい場合は`run_venv_python.bat`を利用してください。


### なぜこの運用方法にしたのかについて
今回使用したライブラリ `h5py` は、iRICのPythonにもインストールされています。しかし、依存の関係上、iRICのPythonインタプリターでは動作しない可能性があるため、別途仮想環境を作成して依存関係を管理するようにしています。
こちらについてはiRICのMinicondaが問題の可能性も考慮できるため現在開発者へ問い合わせをしている状況です。解決したら運用方法を変更する予定です。


### 開発時の注意点
本プロジェクトではバッチファイルを利用している観点から、エンコードと改行コードに気を付ける必要があります。
WindowsではバッチファイルのデフォルトエンコーディングはCP932（Shift-JIS）、改行コードはCRLFです。
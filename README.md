# iric-solver-CgnTM（CGNS-Timestep-Merger）
 - iRICの結果を `result/Solution*.cgn` タイムステップごとに出力したCGNSを束ねるソルバー
 - **[ユーザーマニュアル](https://Pckk-iRIC.github.io/iric-solver-CgnTM/)** で詳細説明

## プロジェクト概要
- iRIC v4 で動作するソルバーです。
- iRIC v4 の分割出力（Solution*.cgn）を統合し、Case1.cgn 相当の時系列CGNSを生成する。
- 入力は `.ipro` / プロジェクトフォルダ / resultフォルダに対応し、出力はプロジェクトまたは単一CGNS。
- 出力ファイル名は `Case1.cgn` または別名を指定できる。
- 分割出力によるファイル増加を抑え、管理・共有・再利用をしやすくすることが目的。

## 主な構成
- `src/` : ソルバーソースコード（definition.xml、実行バッチ、ワーカー）
- `docs/user/` : ユーザー向けマニュアル（MkDocsソース）
- `docs/internal/` : 開発・調査用ドキュメント

## ソルバー名
`CgnTM` で運用する。

## 配置
- 開発: リポジトリ直下の `src`
- 本番: `C:\Users\<username>\iRIC_v4\private\solvers\`

# iRIC環境の注意点
- iRICのインストール時に Miniconda3 もインストールする必要があります。
- Miniconda3 の存在確認は `C:\Users\<username>\iRIC_v4\Miniconda3` を参照してください。

## ダウンロード方法
Releasesページから最新版のページを開き、Assetsからダウンロードしてください。
[Releasesページリンク](https://github.com/Pckk-iRIC/iric-solver-CgnTM/releases)

## ドキュメント
 - [ユーザー用ドキュメント](./docs/user/index.md)
 - [開発者用ドキュメント](./docs/internal/developer_doc.md)

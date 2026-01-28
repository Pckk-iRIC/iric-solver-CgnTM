# CGNS構造差分レポート（簡易）

## 対象
- `tree_Case1_input.txt`
- `tree_Case1.txt`
- `tree_solution1.txt`

## 1. 全体的な違い（要約）
- `tree_Case1_input.txt` は **計算条件・地形などの設定系が中心**で、**BaseIterativeData が無い**。
- `tree_Case1.txt` は `tree_Case1_input.txt` に加えて **BaseIterativeData（TimeValues など）を持つ**。
- `tree_solution1.txt` は **解の本体（FlowSolution 等）とポインタが中心**で、**計算条件等はほぼ空**。

## 2. `tree_Case1_input.txt` の特徴
- `iRIC/CalculationConditions` や `GeographicData`、`GridComplexConditions` が **フルに存在**。
- `iRIC/iRICZone/GridCoordinates` など **格子情報は保持**。
- **BaseIterativeData が存在しない**（`TimeValues`等無し）。

## 3. `tree_Case1.txt` の特徴
- `tree_Case1_input.txt` の構造に加えて、
  - `iRIC/BaseIterativeData`
  - `iRIC/BaseIterativeData/TimeValues`
  - `iRIC/BaseIterativeData/discharge(m3s-1)`
  - `iRIC/BaseIterativeData/domain_area[m2]`
  が追加されている。
- つまり **時系列の基準情報が入っている Case1**。

## 4. `tree_solution1.txt` の特徴
- `FlowSolution1`, `FlowCellSolution1`, `FlowIFaceSolution1`, `FlowJFaceSolution1` が存在。
- `ZoneIterativeData` の **各種ポインタ（FlowSolutionPointers 等）が存在**。
- `GridCoordinatesForSolution1` があり、**解用の格子座標を保持**。
- 一方で `CalculationConditions` / `GeographicData` は **空のグループのみ**で、詳細な入力条件は入っていない。

## 5. まとめ（違いの意味合い）
- `tree_Case1_input.txt`  
  → **入力条件・格子定義中心**（結果時系列は無し）
- `tree_Case1.txt`  
  → **入力条件＋時系列情報付き**（統合後や時系列結果向け）
- `tree_solution1.txt`  
  → **1時刻分の結果（解）そのもの**で、計算条件は最小限

## 6. 考察: Solution*.cgn だけで Case1.cgn 相当が作成できる理由
- iRICの可視化に必要な最小要素は **格子座標・結果(FlowSolution)・時刻(TimeValues)** です。
- 分割出力された `Solution*.cgn` には、これらが各ファイル内に含まれるため、束ねれば Case1.cgn 相当を構成できます。
- `CalculationConditions` や `GeographicData` は計算条件の再現や参照用で、**可視化のみなら必須ではありません**。
- ただし iRIC のプロジェクトとして開く場合は `project.xml` などの構成が必要であり、CGNS単体での扱いは iRIC 側の読み込み方法に依存します。

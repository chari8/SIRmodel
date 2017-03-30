# SIR(S)感染症モデルシミュレータ

## 何奴
SIR感染症モデルをグリッドベースでシミュレートする物体です。クソ雑実装なのであしからず。

## 必要な環境
Python3.x系

## Usage
$ python sir.pyで実行

## 使い方

* clear set

	感染0（全て感受性保持）でキャンバスを作成。

* random set

	ランダムな感染グリッドを持つキャンバスを作成。初期感染率は0.1%。

* 再生・停止・巻き戻し

	それぞれに対応。
	
* Grid

	グリッドの形を三角、四角から選択。
	
* Model

	SIR, SIRSモデルから選択。
	
* Prob

	ステップごとに隣接するグリッドへ感染する確率p。一般的な感染率は三角の場合
	$$
	\begin{eqnarray}
	1 - (1 - p)^3
	\end{eqnarray}
	$$
	四角の場合
	$$
	\begin{eqnarray}
	1 - (1 - p)^4
	\end{eqnarray}
	$$
	で求められる。
	
* Recover Time

	感染したグリッドが免疫を保持するまでのステップ数。
	
* Restoration Time

	免疫を保持したグリッドが失うまでのステップ数。
	
* Range File Name

	感染範囲を制限するファイル名を指定。無記入・ファイル名が見つからない場合は無視。

### 感染範囲指定について

上からy行目の値を$$x_m1 x_M1 x_m2 x_M2 \cdots x_mn x_Mn$$とすると、座標(x,y)は$$x_m1 < x < x_M1, x_m2 < x < x_M2, \cdots x_mn < x < x_Mn$$の範囲に含まれるならば感染有効とする。

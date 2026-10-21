# ODSP の生物学的発展：飛行動物の個体性は「固定された3D形状」か「環境条件付きの確率分布」か

*evidence ledger / updated 2026-10-21 — observed claims only; not a merged manuscript.*

## 2026-10-21 outcome: repeated fine horizontal flight corridors versus repeated vertical shapes

A new post-outcome exploratory reanalysis compared the **same 25 Rotics 2013 storks and 11 Flack 2014 storks** as the archived 50-km height studies, reading only source GPS x-y/time/identity/speed, without opening altitude values. Source-eligible biological bird lists and 50km bird-day counts were byte-fingerprint checked before any link to frozen per-bird height scores.

**Reference correction was essential.** The initial raw x-y diagnostic compared one focal bird's 5km subcell revisit to an *ANY-of-many OTHER birds* union; its other-fix matches (~70.8%, ~75.0%) were inflated by the number of birds. The corrected metric uses one uniformly weighted, eligible OTHER bird observed in the same 50-km coarse cell on another date.

| Fine 5-km revisit INSIDE qualified 50-km cells | Rotics 2013 | Flack 2014 |
|---|---:|---:|
| Focal bird repeats fine subcell on another UTC day | 54.88% | 47.09% |
| One equally weighted other bird does so | 24.93% | 29.18% |
| **Focal − single other bird** | **+29.96 pp** | **+17.91 pp** |
| Previously frozen centered-height bird-identity signal | positive, p=.001 | unsupported, p=.998 |

The 2013 minus 2014 bird-equal fine-route advantage difference is about **12.04 pp**, but an exploratory 5000 bird-bootstrap 95% interval **−1.07 to +25.32 pp includes 0**. Do not claim a significant between-cohort ecological effect.

The equal-other reference's bird-level geographic advantage is positively rank-associated with previously fixed bird height ID scores in the 2013 cohort (Spearman **rho +0.398**, bird bootstrap95 **+0.065 to +0.626**, exploratory age-block label p **0.0426**). The 2014 cohort gives rho **+0.527** but bird bootstrap95 **−0.256 to +1.0** and exploratory label p **0.0953** (11 birds), so there is **no replicated statistically secure rank association**. Both effects are POST-OUTCOME exploratory; do not promote p values as prespecified mechanism evidence. Other bird tracks may have differing GPS effort, so reference correction is not perfect donor-matched calibration.

**Key biological boundary:** Cross-day fine horizontal route reuse is present in both migration studies, yet fixed individual vertical shape identity is supported in only one. Thus route recurrence alone does not guarantee temporal recurrence of the altitude distribution; atmospheric opportunity, travel stage, nestling experience, terrain, sampling support and tag errors remain competing, **untested causal** mechanisms.

[Corrected mechanistic synthesis](https://github.com/zuizui0223/odsp/blob/diagnostic/stork-fine-route-equal-bird-20261021/prospective/STORK_ROUTE_VS_VERTICAL_INDIVIDUALITY_BIOLOGICAL_SYNTHESIS_V1.md) · [machine-readable result and source audit](https://github.com/zuizui0223/odsp/blob/diagnostic/stork-fine-route-equal-bird-20261021/prospective/STORK_EQUAL_OTHER_BIRD_CORRECTION_RESULT_RECEIPT_V1.json) · [source run](https://github.com/zuizui0223/odsp/actions/runs/39530359254).

**Next legitimate scientific test:** In a new independent tracking source, compare date-heldout `P(relative altitude | fine GPS location, date/airmass wind & uplift, flight behavior)` with the addition of animal ID and then animal×weather interaction. Freeze matching/quality/thresholds before opening that source's height values. Do not re-mine the opened 2013/2014 height data in search of a preferred conclusion.

---


## 結論

ODSP から派生した `batter` と `mina` を、単に「飛べる哺乳類」と「飛べない鳥」という二例の普遍法則として扱うことはできない。しかし、**`batter` の個体内反復する鉛直利用形状という問い**は、カモメと渡り鳥のコウノトリへ拡張でき、異なる飛行・移動生態において個体識別情報が残ることを外部データで検証できた。

新しく、`LBBG_ZEEBRUGGE` の2年間では**同じ個体の鉛直高度分布を、その個体の過去の観測と広域の風条件を組み合わせると、風を無視する参照より予測しやすい**と示された。これは個体差の存在検定より生態学的に具体的な進展である。

ただし既存データが示すのは「個体の風に対する反応が個体ごとに異なる」ことではない。全個体が共有する風反応でも、個体別の風条件付き分布の予測利得は生まれ得る。**個体×環境の相互作用は独立に検定する必要がある。**

## 支持済み観測の対応表

| 系 | 生物学的観測単位 | 応答と空間尺度 | 支持済みの推論 | 主な境界 |
|---|---|---|---|---|
| `batter` コウモリ | 個体×独立追跡セッション | 5 km水平セルにおける日/セッション中央値中心化後の高度分布形状 | 4分類群の6パネル中、比較5パネルで全分布の個体ラベルに結び付く反復信号。焦点 `Tadarida` は形状検定を通過しない | 個体とセンサー、行動混合、微小水平移動の差 |
| `odsp` DELTATRACK カモメ | 個体×日 | 5 kmでのGPS高度分布形状 | *Larus fuscus* 40鳥、899鳥日、66,811 GPS。帰無補正利得 +0.07356、Holm p=.002 | 同個体の低速記録でも個体ラベル信号。装置IDと鳥IDを分離できない |
| `odsp` Zeebrugge カモメ | 個体×日×地域風レジーム | 5 kmでの同一個体の「風条件あり/なし」高度分布モデル比較 | *L. fuscus* 2016年39鳥・744鳥日 +0.03452（p=.001）、2017年24鳥・422鳥日 +0.04281（p=.001）。2年の異なる鳥は52、重複11 | 風はCERRAの繁殖拠点周辺の広域値。飛行中の気流・風因果・飛行モードは未測定 |
| Rotics コウノトリ | 個体×日（成鳥/幼鳥を保持） | **50 km**回廊セルにおける中央値中心化後の楕円体高分布 | *Ciconia ciconia* 2013年25鳥・111鳥日・6,951 GPS。観測利得 +0.01648、帰無平均 −0.17837、差 +0.19485、片側p=.001。5 km同条件の対象は0鳥 | 50 kmはカモメとは別の尺度・選定された新エンドポイント。実標高・鳥の行動と装置誤差を分離できない |
| `mina` ペンギン | 繁殖個体群×繁殖モニタリング区画×年 | 個体数減少に対する区画間構成の再配分 | 5個体群単位でinverse-Simpsonの有効区画数が19–83%減少、計数誤差と比例的個体数減少だけでは説明しにくい | 個体の鉛直空間利用ではない。直接の3D/風応答比較は禁止 |

**異なる推定量のnatsを、分類群の生物学的「個体特殊化の強さ」として横並びにしない。**

## 数理的な上位仮説

個体 (i)、空間セル (x)、時間/行動状態 (t)、独立して得た環境文脈 (E)、そのセッション中央値からの相対高度 (z_c) について、

```
P(z_c | i, x, t, E)
```

を対象とする。「固定個体形状」なら、環境文脈 (E) を変えても個体ごとの形状は同じであり、条件付きモデルに追加予測利得は生まれない。環境可塑性がある場合は (E) により分布の幅・裾・質量配置が変わり得る。

ただし**三つの生物学的質問**を分ける必要がある。

1. **個体対応の反復性** — 同じ環境/セルで、自己の別日データは別個体のデータより予測しやすいか（`batter`、DELTATRACK、Rotics 2013）。
2. **環境による共有変化** — 全個体が共通に持つ風反応で、鉛直分布形状に追加の予測情報が得られるか（Zeebrugge 2016/17 の現実的な説明候補）。
3. **個体特異的な環境応答** — 共通の風反応を除去しても、個体 (i) に固有の風感受性の形が別日に転移するか（**未検証**）。

上記3を示さなければ「個体ごとに異なる風への対応戦略」ではなく、**個体IDの反復信号と、同じ種に広く共有される環境依存性が共存する**という控えめな主張に留める。

なおこれらは有限データ上のheld-out log-score と帰無分布の比較であり、真の条件付き相互情報量そのものを直接推定したことにはならない。

## 特殊性について、実際に分かったこと

コウモリやカモメの中心拠点型採餌は、同じ場所を別日にも通りやすく、5 kmの共通セル比較が可能になる。長距離を渡るコウノトリでは、同じ2013年の位置データでも5 kmセルで2日以上・他鳥との支持がある個体は**0**、50 kmなら**25**、100 kmなら**55**になる。この差は、**空間尺度の選び方と移動生態が、個体性の識別可能性を左右する**という強い境界を示す。

ただしこれが「移動が長距離ほど個体性そのものが消える」ことの証拠ではない。狭いセルへの再訪が少ないためデータ比較が成立しにくいのであって、実際の鉛直戦略の有無とは別である。

コウノトリの事前固定50 km結果では、帰無検定の集団数は観測25羽に対して36–53羽。未較正の鳥別スコアが正の鳥は**13/25羽**だけで、全体の帰無相対陽性を「全鳥に均一な正の特殊化」と読むことはできない。年齢別未較正平均は成鳥−0.0308、幼鳥+0.0480だが、**年齢差の確証を与える検定は行っていない**。

## 新しい重要な境界：独立したコウノトリ集団では同じ結果にならなかった

同じ50 kmセル・同じ中央値中心化GPS楕円体高分布・同じ日付×年齢層内のwhole-session交換帰無を使い、別Movebank原研究（Flack 2014）の**巣内雛由来11個体**で、Rotics 2013年の陽性を独立に追試した。両原研究の参照表で生物学的動物IDの完全一致は**0**（GPSタグIDは全体で1台再利用、最終解析鳥には該当しない）。

| 50 km渡り鳥検定 | Rotics 2013 | Flack 2014 |
|---|---:|---:|
| 最終解析鳥 | 25（成鳥10・幼鳥15） | 11（装着時は巣内雛のみ） |
| 評価鳥日・GPS fix | 111・6,951 | 33・2,039 |
| 原スコア（自己−他個体） | +0.01648 | **−0.26989** |
| 999交換の帰無平均 | −0.17837 | −0.13524 |
| 観測−帰無平均 | **+0.19485** | **−0.13466** |
| 片側p | **0.001** | **0.998** |
| 未較正の正スコア鳥 | 13/25 | **2/11** |

両検定の999帰無は全て有効。高度欠測は小さく（各年有効率99.98%）、事前に固定した観測条件に届かなかったという理由ではない。ただし2014年は最終11個体で、許容検出力・移動回廊・出発地・齢期・タグ精度は2013年と違う。**p=.998は正の個体性仮説の不支持であり、個体性の存在しないことを示す同等性検定ではない。**

これは、普遍的な「飛ぶ動物の固定的個体形状」が示されたという解釈を否定的に再検討させる。**固定形状が現れる条件**（反復する機会・行動状態・標高地形・気象・観測品質）が本質的な生態学的問いになった。ただしこの2コホートの差そのものの有意検定や機構同定は**していない**。帰無ラベルの交換により評価個体集合が変化（Rotics観測25 vs帰無36–53、Flack観測11 vs帰無13–28）することも留保する。

- [別研究群の固定検定と生態学的な対比](https://github.com/zuizui0223/odsp/blob/prospective/stork2014-independent-cohort-20261020/prospective/WHITE_STORK_2013_2014_CROSS_COHORT_BIOLOGICAL_SYNTHESIS_V1.md)
- [Flack 2014 機械可読レシート](https://github.com/zuizui0223/odsp/blob/prospective/stork2014-independent-cohort-20261020/prospective/FLACK_STORK_2014_50KM_RESULT_EVIDENCE_RECEIPT_V1.json) · [実行成功](https://github.com/zuizui0223/odsp/actions/runs/39416255916)

## 次に検証すること

1. **反復する生態的課題を外部データで測る。** 同じ飛行条件/大気上昇流/相対高度選択を複数の日に経験できる度合い（条件の反復可能性）と、個体の高度形状の転移性が結び付くかを、未開封の独立研究で予備固定する。
2. **個体×環境交互作用を共有反応から分ける。** `P(z|個体,風)` の利得だけでは共通の風反応と個体特異的な風応答は分離できない。共通の風効果モデルを対照にする。
3. **機器と地形の交絡を切り離す。** GPS楕円体高に対しDEM、センサー精度、独立飛行モード推定、可能ならタグ交換を外部の基準として組み込む。

元の2013/2014年コウノトリを条件調整して再度「成功」させる解析は行わない。ペンギンの繁殖区画集中は個体レベルの鉛直空間組織とは異なる問いとして保持する。

## 生態学的な新しい知見と方法上の限界の区別

- 生物学的に検証されたもの：飛行する哺乳類だけでなく、2目の鳥の追跡データで個体ラベルに結び付く高度確率分布形状が別日に反復する。カモメでは地域風条件を加えると形状予測の利得が2年間で再現する。
- 識別可能性として分かったもの：拠点型と渡り型では、同じ水平セルへ戻る条件が異なるため、必要な空間粒度が変わる。個体/装置/行動混合、地形を除去した真の生物学的寄与割合は未確定。
- まだ検証されていない一般法則：世界の飛行動物に個体別の異なる風反応がある、適応的鉛直ニッチ分割を行う、ペンギンの区画集中が同じメカニズムで起きる、という主張。

### 実行根拠

- `batter` [current README](https://github.com/zuizui0223/batter/blob/main/README.md)
- `odsp` [DELTATRACK flight positive and low-speed caveat](https://github.com/zuizui0223/odsp/blob/prospective/biological-generality-20261019/prospective/CURRENT_STATUS.md)
- [Zeebrugge 2016–2017 wind shape evidence](https://github.com/zuizui0223/odsp/blob/prospective/zeebrugge-2017-temporal-wind-test-20261020/prospective/ZEEBRUGGE_2016_2017_WIND_HEIGHT_BIOLOGICAL_SYNTHESIS_V1.md)
- [Stork 2013 complete frozen result](https://github.com/zuizui0223/odsp/actions/runs/39409175819) and [deterministic rerun](https://github.com/zuizui0223/odsp/actions/runs/39413456822)
- [Stork 2013 evidence receipt](https://github.com/zuizui0223/odsp/blob/prospective/stork2013-50km-vertical-identity-20261020/prospective/WHITE_STORK_2013_50KM_RESULT_EVIDENCE_RECEIPT_V1.json)
- `mina` [current README](https://github.com/zuizui0223/mina/blob/main/README.md)

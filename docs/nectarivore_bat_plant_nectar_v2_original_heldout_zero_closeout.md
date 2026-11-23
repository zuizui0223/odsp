# Bat-camera × nectar quantity: source-verified 9-plant heldout outcome (2026-11-23)

**Status: real original source + pre-outcome model, NO additional predictive information under the frozen nectar model.** This is an observational local result; neither a null proof of nectar ecology nor a biological 3D SDM.

## Original public evidence and prior art

Thiel et al. (2024), *Vertically stratified interactions of nectarivores and nectar-inhabiting bacteria in a liana flowering across forest strata*, American Journal of Botany DOI `10.1002/ajb2.16303`. Original public Zenodo **10.5281/zenodo.10527420**, v2. Authors already reported increased bat and bird visitation in midstory and correlations with available flowers and nectar quantity/quality, so a naive descriptive resource–visitation association would be **prior art**, not new discovery.

Original files checksum-authenticated, original datasets are **one liana species *Marcgravia longifolia*** in one forest:
- `CameraTraps.xlsx` MD5 `473bb5273b8f2e5369b4bfca0385b829`, SHA256 `b96a6c13e6826c284a32457cd680382cd855ad5bf34959e5695b7a2cfae84d1a`, 180 original data rows.
- `Nectar measurements_Strata.xlsx` MD5 `85e2a40e1a61421e19f86219fff87f9a`, SHA256 `29eb9197c9c28b8083c2a646ed5e3389bffa764566a6fdc8c673e6c0f43647cc`, 40 original data rows.
- `Mist-netting_bats.xlsx` original MD5 `777acca28e0f59fc0103aac35daef92a`, SHA256 `9c5e402cc7cc6cd95b0e4ab1f5a306b0cc821905cd0ec27c619ca4b6af90b780`, 127 original data rows; **not** used as Bat camera visit/effort response.

Original author Data Explain fields: `ML_ID` is *Marcgravia* individual in both source tables; visit Camera `ML03` and resource Nectar `3` are equivalent original numeric plant IDs. Camera `Abundance` is number of animal visits, `Hours` actual camera hours, `Capture_rate=Abundance/Hours`. Camera Bat/Moth/Marsupial observational method is wildlife camera; Bird is a separate focal human method and was excluded from Bat-camera model. Nectar source `Nect_quant_mean` is mean nectar quantity of sampled flower nectaries per source layer, with two reported resource years 2018/2019, while camera original Data has no Year/Date column. **These cannot be treated as temporally synchronized paired nectar and visits.**

## Source gates and pre-outcome corrections, in exact audit order

1. [v1 first authentic XLSX source gate #45095211194](https://github.com/zuizui0223/odsp/actions/runs/45095211194): all three original MD5/SHA256 and headers matched. Biological count/nectar outcomes unopened.
2. [v1.1 exact plant+stratum key/effort #45095433472](https://github.com/zuizui0223/odsp/actions/runs/45095433472): 29 original Camera ID strings, 10 original Nectar ID strings, zero exact common IDs, Camera Hours source missing/non-numeric in 14 rows. Scientific SOURCE_HOLD, before outcomes.
3. [v1.2 author original ID/Explanation grammar #45095602602](https://github.com/zuizui0223/odsp/actions/runs/45095602602): original Camera MLnn vs Nectar n is source-ID spelling; same documented biological *Marcgravia* individual. No outcomes.
4. [v1.3 canonical plant mapping+Bat-only source effort #45095799669](https://github.com/zuizui0223/odsp/actions/runs/45095799669): 10 plants and 28 layers canonically matched across camera/nectar; Bat-camera positive Hours and Inflorescences combined with nectar gives 26 eligible *source pairs across all 10 plants*; 9 plants have >=2 paired strata and 7 of those have all 3. Nonpositive/nonnumeric Bat camera Hours in 8 rows and Inflorescences in 9; these non-operational source layers were excluded by source metadata eligibility, **not assigned zero visits**. Source-level strict original full-record criterion HOLD.
5. [v2 PRE-OUTCOME scoring freeze](nectarivore_zenodo_bat_nectar_plant_holdout_v2_preoutcome.md) committed before opening `Abundance` or `Nect_quant_mean`; only original Bat camera entries on positive source effort, exact plant/stratum paired nectar, leave whole plant out; identical source exposure Hours×Inflorescences for both models; B0 layer-specific parameters, B1 adds beta×log1p(mean Nectar); 9-point grids for each parameter in [-2,2], step 0.5, fixed B1 L2 penalty 0.02 beta². Entire original plant is a fold. This model is **not** an adapted/tuned SDM for individual bat altitude.
6. First v2 [run #45096279570](https://github.com/zuizui0223/odsp/actions/runs/45096279570) **SOURCE_STRUCTURE_STOP** before parsing numerical biological fields because it mistakenly required 26 *eligible* cells **within the 9 plants**. The v1.3 original structure shows 7×3+2×2=**25 eligible strata across 9 plants**, plus a singleton tenth plant giving 26 across all 10. No ecological response had been read in the code path, so a separate [pre-outcome arithmetic amendment](nectarivore_v2_preoutcome_25cell_source_arithmetic_amendment.md) was committed and the frozen **structural count** was corrected to 25. Scientific model, covariates, penalties, test folds and plant eligibility **unchanged**. A source-free synthetic regression test now covers 180 Camera/40 Nectar rows with 9 eligible/25 strata and tenth singleton excluded.
7. First full original source outcome [CI #45096400185](https://github.com/zuizui0223/odsp/actions/runs/45096400185), artifact **14783467426**, successfully computed original numeric `Abundance` and `Nect_quant_mean`. After synthetic regression was added, scientifically unchanged [CI #45096424398](https://github.com/zuizui0223/odsp/actions/runs/45096424398) independently repeated the frozen source/model and also completed successfully. Original trial’s zero effect was not selected/changed.

## First original numerical result: nectar adds exactly no heldout predictive score

**Exactly nine original *Marcgravia* individuals, 25 observed Bat-camera × source height cells, 5,421 counted Bat camera visits.** Source `Abundance` confirmed nonnegative integer; original `Nect_quant_mean` valid positive/zero wherever source-admitted. Source plant total camera visits all positive, all nine folds estimable.

| Matched heldout target | Original source result |
|---|---:|
| B0 = height layer + Hours×Inflorescences offset, 9 leave-one-plant-out folds | **−0.9358847345782975 nats/recorded visit** |
| B1 = same + log1p(original nectar quantity) coefficient | **−0.9358847345782975 nats/recorded visit** |
| **B1−B0** | **0.0 nats/recorded visit** |
| Number of heldout original plants with improvement | **0/9** |
| Whole-plant descriptive 95% bootstrap | [0.0,0.0] |
| Frozen category | `all-nonpositive` (all exact zero) |
| B1 train-only fitted beta in every fold | **0.0** |

**Interpretation:** B1 actually chose `beta_nectar=0` during **every training-only optimization**, so the two models became **identical**. This is NOT a posterior detection of ecological independence or a proof that adding nectar measurements can never help; it is only an unambiguous **model-specific result** under this predeclared β grid and ridge penalty, current original count/effort qualification, and 9 plant-heldout data. No α or β retuning, selecting another resource field (sugar/pH), changing camera denominator or plant subset is authorized after this outcome. In particular **do not claim "95% CI establishes exact null or equivalence"**: the bootstrap degenerates because the model fell back to B0 in all 9 folds, and the fitted beta grid included 0. With so few plants and source variability, the data do not establish a general mechanistic absence.

## Additional limitations

- Original source paper already found a nectar association; this is an external **predictive target** using LOO plant, not contradiction of original within-study nectar correlations or new source-independent ecological replication.
- `Hours×Inflorescences` is a working opportunity-offset model; the author's original `Capture_rate` is per **Hours only**. We do not claim source-calibrated proportional nectar availability or visibility/detection.
- Year 2018/19 resource rows are averaged across original years; camera rows have no matching calendar year. Cannot claim same-night food-choice effects or temporal resource tracking.
- Bat source `Taxa` is **one pooled Bat class**, not a species-resolved set of bat species; sampling `Stratum` identifies **camera position around source plants**, not 3D individual bat flight coordinates. Other Animal methods from Bird are focal observation and not comparable without modality-specific q/effort.
- Camera hours missing in some Bat rows, especially higher strata; inclusion is conditional on observed camera operation. Missing source effort is not a true zero visit. Independent plant identities within one forest are not independent regional/site replicates.
- The underlying original source is observational; no causality, detector probability q, actual bat 3D SDM, general new-forest transfer, species-specific competition or pollen/nectar intake can be concluded.
- This is a *negative/boundary outcome for the fixed model*, scientifically important for avoiding overclaiming resource-conditional higher-dimensional SDMs. Source-backed software and archived exact source receipts remain reproducible without original raw workbooks being committed to this derivative repo.

**Status:** Completed source admission and scoring; need independent implementation / audit of Beta=0 before final claim promotion. All frozen `odsp/main` N2, batter JAE, esdm E5 and Drafts #306–308 untouched.

# Cover letter draft — Methods in Ecology and Evolution — state-prediction v6

> Replace bracketed administrative placeholders only after the author team confirms them. The scientific claims below are bounded by the validated v5 evidence and should not be strengthened without new evidence.

Dear Editors,

Please consider our Research Article, **“State-resolved ecological prediction: from flat suitability to transferable ecological-state distributions,”** for publication in *Methods in Ecology and Evolution*.

Ecological prediction is commonly returned as one scalar per place, such as suitability, occurrence probability or use. Yet organisms can occupy distinct height, depth, time, phenological or behavioural states under otherwise similar mapped conditions. We introduce ODSP as a model-agnostic framework that changes the prediction target from a collapsed scalar to a probability distribution over explicitly declared ecological states, `P(A|X)`, and then asks whether that added state resolution improves prediction in prospectively independent groups.

The methodological contribution is **not** a workflow that merely links existing prediction algorithms. The upstream learner is deliberately exchangeable. ODSP instead defines a learner-agnostic prediction-and-evidence object comprising: (i) an explicit ecological-state probability target `P(A|X)`; (ii) a lower-information training-marginal comparator `P(A)`; (iii) independent-group log-score transfer gains that preserve individuals or sites as evidential units; and (iv) a predeclared fail-closed distinction among generalizing, non-generalizing, mixed and unavailable outcomes. Random forests and multinomial regression are demonstration engines rather than the methodological contribution itself.

We validate predictive behavior before empirical application. Across 128 replicates at each tested sample size, stable state organization produced positive held-out gain in every replicate, deliberately shifted organization produced negative gain in every replicate, and unorganized state support converged toward zero gain as sampling increased. The finite-discrete information implementation also passed 1,873 representation and information-law obligations with zero failures.

We then execute two public-data state-prediction endpoints whose source archives, state bins, predictors, independent groups, model settings and terminal rules were frozen before outcome access. The first, using MH_ANTWERPEN marsh-harrier tracking, contained 193,370 thinned events but only three eligible independent individuals against a frozen minimum of four; it therefore closed as unavailable before transfer scoring. The second used the fixed BOP_RODENT v3 raptor archive and admitted 154,655 events from 30 individuals across four species. Random-forest state predictions improved held-out log score over the pooled training marginal for 27 of 30 individuals and improved multiclass Brier score for all 30. Under the predeclared all-individual rule, the terminal result remains mixed because three individuals had non-positive primary gain.

Because species identity was itself a predictor in the BOP model, v6 reports two explicitly post-outcome descriptive audits of the already frozen primary gain. Across the 30 held-out individuals, the mean total gain of `0.57091` nats/event decomposes into a pooled-to-species baseline component of `0.07279` and a within-species context component of `0.49812`. For *Circus pygargus*, `0.93237` of the `1.24613` mean gain is the within-species context component; *Buteo buteo* shows the contrasting pattern, with a positive species component and slightly negative mean within-species context component. This decomposition did not refit the model, re-access raw tracking data, retune any setting, replace the prospective comparator or change the 27/30 mixed terminal decision. A second descriptive population summary treats held-out individuals as equal-weight groups and species as the resampling cluster. The total frozen gain averaged `0.57091` nats/event with a species-cluster bootstrap interval of `[0.23969, 1.04119]`; 27/30 individuals were positive, while a labelled new-individual prediction interval still crossed zero. We report these quantities to describe effect magnitude, prevalence and heterogeneity, not to reclassify the prospective endpoint. Only four species clusters are represented, so cluster-level uncertainty is explicitly treated as descriptive.

Earlier Tawaki, European free-tailed bat and Snapshot Serengeti analyses are retained as supporting diagnostics rather than relabelled as new prediction demonstrations. Together they show why estimability, added-state structure and independent transfer must remain distinct evidential layers.

We believe the manuscript fits *Methods in Ecology and Evolution* because the methodological gap and solution are independent of the example organisms. The same prediction object and validation logic can target altitude layer, depth, time, phenophase, behaviour, microhabitat or joint states and can sit above different probabilistic learners. The empirical applications demonstrate use and failure modes; they are not the basis of the novelty claim. The manuscript also states its limits explicitly: the current evidence does not establish causal drivers, a fundamental niche, height above ground from absolute altitude, universal positive transfer, or automatic downstream state maps.

For double-anonymous peer review we provide a deterministic scientific-only code-and-evidence archive containing the state-prediction core, prospective contracts, known-truth tests, selected endpoint QA, sanitized scientific summaries, the BOP decomposition code/evidence and the anonymous v6 manuscript. Governance/provenance infrastructure from the full development repository and raw receipts carrying internal workflow identifiers are excluded. The archive is identity-scanned, installed and tested in continuous integration.

The study uses publicly archived data and involved no new animal capture, handling or field intervention. Ethical approvals and permits for original data collection remain those reported by the corresponding source studies and archives. Generative-AI assistance is disclosed transparently, including the application/model version used; all scientific decisions, validation and final responsibility remain with the authors.

[AUTHOR CONFIRMATION REQUIRED: This manuscript is not under consideration elsewhere, all authors have approved its submission, and reuse terms or permissions for every third-party dataset used in the manuscript have been confirmed.]

Thank you for considering the manuscript.

Sincerely,

[CORRESPONDING AUTHOR NAME]  
[INSTITUTION]  
[EMAIL]

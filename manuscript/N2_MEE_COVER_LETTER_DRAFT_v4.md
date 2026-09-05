# Cover letter draft — Methods in Ecology and Evolution — state-prediction v4

> Replace bracketed administrative placeholders only after the author team confirms them. The scientific claims below are bounded by the validated v4 evidence and should not be strengthened without new evidence.

Dear Editors,

Please consider our Research Article, **“State-resolved ecological prediction: from flat suitability to transferable ecological-state distributions,”** for publication in *Methods in Ecology and Evolution*.

Ecological prediction is commonly returned as one scalar per place, such as suitability, occurrence probability or use. Yet organisms can occupy distinct height, depth, time, phenological or behavioural states under otherwise similar mapped conditions. We introduce ODSP as a model-agnostic framework that changes the prediction target from a collapsed scalar to a probability distribution over explicitly declared ecological states, `P(A|X)`, and then asks whether that added state resolution improves prediction in prospectively independent groups.

ODSP is not proposed as a new MaxEnt- or random-forest-style occurrence algorithm. Different probabilistic learners can generate the state distribution; ODSP supplies a common response representation, a lower-information training-marginal comparator, and an independent-transfer scoring architecture. The primary score is held-out log-score gain over the training marginal state distribution, with multiclass Brier improvement, top-1 accuracy and probability assigned to the realized state as complementary diagnostics. Independent individuals or sites are retained as separate evidential units so a large group cannot rescue a conflicting transfer failure through pooled observation mass.

We validate the predictive behavior before empirical application. Across 128 replicates at each tested sample size, stable state organization produced positive held-out gain in every replicate, deliberately shifted organization produced negative gain in every replicate, and unorganized state support converged toward zero gain as sampling increased. The underlying finite-discrete information implementation also passed 1,873 representation and information-law obligations with zero failures.

We then execute two public-data state-prediction endpoints whose source archives, state bins, predictors, independent groups, model settings and terminal rules were frozen before outcome access. The first, using MH_ANTWERPEN marsh-harrier tracking, contained 193,370 thinned events but only three eligible independent individuals against a frozen minimum of four; it therefore closed as unavailable before transfer scoring. The second used the fixed BOP_RODENT v3 raptor archive and admitted 154,655 events from 30 individuals across four species. Random-forest state predictions improved held-out log score over the training marginal for 27 of 30 individuals and improved multiclass Brier score for all 30. Under the predeclared all-individual rule, the terminal result remains mixed because three individuals had non-positive primary gain. This combination is useful methodologically: the framework can expose strong average predictive value without erasing genuine failures of individual-level transfer.

Earlier Tawaki, European free-tailed bat and Snapshot Serengeti analyses are retained as supporting diagnostics rather than relabelled as new prediction demonstrations. Together they show why estimability, added-state structure and independent transfer must remain distinct evidential layers.

We believe the manuscript fits *Methods in Ecology and Evolution* because it provides a reusable prediction-and-evaluation architecture rather than a taxon-specific ecological result. The method can sit above different probabilistic learners and can in principle target altitude layer, depth, time, phenophase, behaviour, microhabitat or joint states, provided the state semantics and validation units are defensibly declared. The manuscript also states its limits explicitly: the current evidence does not establish causal drivers, a fundamental niche, height above ground from absolute altitude, universal positive transfer, or automatic downstream state maps.

For double-anonymous peer review we provide a deterministic code-and-evidence archive containing the state-prediction core, prospective contracts, known-truth tests, selected endpoint QA, sanitized scientific summaries and the anonymous manuscript. Raw terminal receipts carrying internal repository/workflow provenance are excluded. The archive is identity-scanned, conservatively annotates submitted Python files for generative-AI assistance, and is independently extracted, installed and tested in continuous integration.

The study uses publicly archived data and involved no new animal capture, handling or field intervention. Ethical approvals and permits for original data collection remain those reported by the corresponding source studies and archives. Generative-AI assistance is disclosed transparently; all scientific decisions, validation and final responsibility remain with the authors.

[AUTHOR CONFIRMATION REQUIRED: This manuscript is not under consideration elsewhere and all authors have approved its submission.]

Thank you for considering the manuscript.

Sincerely,

[CORRESPONDING AUTHOR NAME]  
[INSTITUTION]  
[EMAIL]

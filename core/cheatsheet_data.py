"""Curated reference tables for ML fundamentals.

Each section is a dict with:
  - description: short intro shown above the table
  - columns:     header row
  - widths:      CSS widths for the columns (must sum to ~100%)
  - rows:        list of rows, each a list of strings matching `columns`

Sections covering an *algorithm* pass ``with_how=True`` to prepend a
"How it works" column; metric / validation / technique tables omit it.

Rendered as an HTML table by views/cheatsheet.py. Avoid raw `<`, `>`, and
`&` in cell text so the generated HTML stays valid.
"""

_BASE_COLS = ["Why it's different", "When to use", "Advantages", "Drawbacks"]

# 5 columns (no "How it works") — used by the metric / technique tables.
_WIDTHS_5 = ["14%", "24%", "20%", "21%", "21%"]
# 6 columns (with "How it works") — used by the algorithm tables.
_WIDTHS_6 = ["11%", "20%", "17%", "18%", "17%", "17%"]


def _section(name_col, description, rows, with_how=False):
    if with_how:
        columns = [name_col, "How it works", *_BASE_COLS]
        widths = _WIDTHS_6
    else:
        columns = [name_col, *_BASE_COLS]
        widths = _WIDTHS_5
    return {
        "description": description,
        "columns": columns,
        "widths": widths,
        "rows": rows,
    }


CHEATSHEETS = {
    # ------------------------------------------------------------------ #
    #  Supervised — classification
    # ------------------------------------------------------------------ #
    "Classification": _section(
        "Algorithm",
        "Predict a discrete label. Choose based on data size, "
        "interpretability needs, and whether the boundary is linear.",
        [
            ["Logistic Regression",
             "Fits a linear score wᵀx + b, squashes it through a sigmoid (binary) or softmax (multiclass), and minimizes log loss.",
             "Linear decision boundary with a probabilistic output.",
             "Baseline for binary or multiclass problems; interpretable coefficients and calibrated probabilities.",
             "Fast, interpretable, well-calibrated, low variance.",
             "Cannot capture nonlinearities or interactions without manual feature engineering; sensitive to outliers and multicollinearity."],
            ["Decision Tree",
             "Repeatedly picks the feature and threshold that best splits the data (by Gini / entropy or variance), growing a tree until a stopping rule is hit.",
             "Recursive axis-aligned splits; non-parametric and rule-based.",
             "When you need a highly interpretable rule set, mixed feature types, or nonlinear relationships.",
             "Interpretable, no scaling needed, captures nonlinearity and interactions.",
             "Prone to overfitting, unstable (small data changes give a different tree), biased toward high-cardinality features."],
            ["Random Forest",
             "Trains many deep trees on bootstrap samples with random feature subsets at each split, then averages (regression) or votes (classification).",
             "Bagged ensemble of decorrelated trees; variance reduction by averaging.",
             "Strong tabular baseline; when you want good accuracy with little tuning.",
             "Robust to overfitting, handles nonlinearity, little preprocessing.",
             "Less interpretable than a single tree, memory-heavy, poor extrapolation, slower inference."],
            ["Gradient Boosting (XGBoost / LightGBM / CatBoost)",
             "Builds trees sequentially; each new tree is fit to the gradient of the loss (the residuals, for squared error) of the current ensemble, scaled by a learning rate.",
             "Sequential ensemble where each tree fits the previous residual; bias reduction.",
             "When accuracy is the priority on tabular data; competitions and production tabular models.",
             "Usually the top performer on tabular data; handles mixed types and missing values.",
             "Many hyperparameters; can overfit if not tuned; harder to interpret; sequential training."],
            ["Support Vector Machine",
             "Finds the hyperplane that maximizes the margin between classes; the kernel trick evaluates dot products in a higher-dimensional space without materializing it.",
             "Finds the maximum-margin hyperplane; kernel trick handles nonlinearity.",
             "Small-to-medium datasets with high dimensionality and a clear margin.",
             "Effective in high dimensions, kernel flexibility, memory-efficient (support vectors only).",
             "Does not scale to large n; kernel and C tuning is expensive; no native probability output."],
            ["k-Nearest Neighbors",
             "At prediction time, finds the k closest training points by a distance metric and returns their majority vote (or average for regression).",
             "Instance-based lazy learner: no training, predicts from the k closest points.",
             "Small, low-dimensional data; simple baseline; very irregular decision boundaries.",
             "No training phase, simple, naturally multiclass.",
             "Slow inference, sensitive to scaling, suffers from the curse of dimensionality, needs a distance metric."],
            ["Naive Bayes",
             "Applies Bayes' theorem and assumes features are conditionally independent given the class, so the joint likelihood factorizes into per-feature terms.",
             "Generative model with a conditional-independence assumption between features.",
             "Text classification (spam, sentiment), small datasets, very high-dimensional sparse features.",
             "Extremely fast, works with tiny data, multiclass by default.",
             "Independence assumption is usually violated; probability estimates are poorly calibrated."],
            ["Neural Network",
             "Stacks linear layers with nonlinear activations; gradients from backpropagation update the weights to minimize the loss.",
             "Stacked nonlinear layers that learn representations; universal approximator.",
             "Large datasets, unstructured data (images, text, audio), complex interactions.",
             "Very flexible, scales with data, learns representations.",
             "Data-hungry, computationally expensive, black-box, many hyperparameters."],
        ],
        with_how=True,
    ),

    # ------------------------------------------------------------------ #
    #  Supervised — regression
    # ------------------------------------------------------------------ #
    "Regression": _section(
        "Algorithm",
        "Predict a continuous target. Watch for linearity assumptions, "
        "outliers, and whether you need interpretability or pure accuracy.",
        [
            ["Linear Regression (OLS)",
             "Solves for the coefficient vector that minimizes the sum of squared residuals; closed form is (XᵀX)⁻¹Xᵀy.",
             "Linear fit minimizing squared error; closed-form solution.",
             "Baseline; roughly linear relationships; interpretability matters.",
             "Fast, interpretable coefficients, closed form, inferential statistics available.",
             "Assumes linearity and homoscedasticity; sensitive to outliers and multicollinearity."],
            ["Ridge Regression (L2)",
             "Same objective as OLS but with λ‖w‖² added, so the solution becomes (XᵀX + λI)⁻¹Xᵀy — more bias, far less variance.",
             "Linear regression with an L2 penalty that shrinks coefficients.",
             "Correlated features; p large relative to n.",
             "Stabilizes estimates, handles multicollinearity, reduces variance.",
             "Does not zero out coefficients, so no feature selection."],
            ["Lasso Regression (L1)",
             "Adds λ‖w‖₁ to the loss; the kink in the L1 penalty at zero drives many coefficients to exactly zero.",
             "Linear regression with an L1 penalty that drives coefficients to zero.",
             "When you want automatic feature selection or a sparse model.",
             "Performs feature selection; interpretable sparse solutions.",
             "Unstable with correlated features; biased estimates."],
            ["Elastic Net",
             "Combines the L1 and L2 penalties with a mixing parameter α, inheriting sparsity from Lasso and stability from Ridge.",
             "Combines L1 and L2 penalties.",
             "Correlated features AND you want sparsity.",
             "Balances Lasso selection with Ridge stability.",
             "Two hyperparameters to tune."],
            ["Polynomial Regression",
             "Expands the feature matrix with powers and interactions of the original features, then fits OLS on the expanded matrix.",
             "Linear regression on polynomial features.",
             "Smooth nonlinear relationships; you still want a linear-in-parameters model.",
             "Captures curvature; keeps closed-form inference.",
             "Easy to overfit; feature explosion; sensitive to outliers at the edges."],
            ["Decision Tree Regressor",
             "Splits recursively on the threshold that most reduces within-node variance, producing a piecewise-constant prediction.",
             "Recursive splits minimizing within-node variance.",
             "Nonlinear relationships, mixed feature types, interpretability.",
             "Interpretable, captures nonlinearity, no scaling needed.",
             "Overfits, unstable, piecewise-constant predictions."],
            ["Random Forest Regressor",
             "Bagged ensemble of regression trees trained on bootstrap samples; the prediction is the average across trees.",
             "Bagged ensemble of trees that averages predictions.",
             "Strong tabular baseline; nonlinear relationships.",
             "Robust, low tuning, handles nonlinearity and interactions.",
             "Cannot extrapolate beyond the training range; memory-heavy."],
            ["Gradient Boosting Regressor",
             "Fits trees sequentially to the negative gradient of the loss (the residuals, for squared error), shrinking each tree's contribution by the learning rate.",
             "Sequential ensemble where each tree fits the residual.",
             "Accuracy-critical tabular regression.",
             "Usually top accuracy on tabular data; handles mixed types.",
             "Hyperparameter-sensitive; sequential training; can overfit."],
            ["Support Vector Regression",
             "Fits a function that deviates from each training target by at most ε; only points outside that ε-tube become support vectors and pull the fit.",
             "Fits an epsilon-insensitive tube around the data; kernel-based.",
             "Small-to-medium data with nonlinear relationships.",
             "Kernel flexibility; robust to outliers via the epsilon-insensitive loss.",
             "Does not scale to large n; kernel / C / epsilon tuning."],
            ["kNN Regressor",
             "Predicts the (optionally weighted) average of the targets of the k nearest neighbors in feature space.",
             "Averages the target of the k nearest neighbors.",
             "Small, low-dimensional data with very local patterns.",
             "Simple, no training, non-parametric.",
             "Slow inference; scaling-sensitive; curse of dimensionality."],
            ["Poisson / Negative Binomial",
             "Fits a GLM with a log link, log(E[y]) = Xw, so predictions are always positive; the mean equals the variance (Poisson) or allows overdispersion (NB).",
             "GLM for count targets with a log link; models the rate directly.",
             "Count data (events, visits) where OLS could predict negative values.",
             "Matches the data-generating process; interpretable rate ratios.",
             "Requires distributional assumptions; overdispersion needs Negative Binomial."],
            ["Quantile Regression",
             "Minimizes the pinball loss for a chosen quantile τ instead of squared error, so the fit tracks that conditional quantile rather than the mean.",
             "Predicts a conditional quantile rather than the mean.",
             "When you care about the median or tails (e.g. P90 demand).",
             "Robust to outliers; produces prediction intervals.",
             "Less familiar; optimization is slower; no closed-form solution."],
        ],
        with_how=True,
    ),

    # ------------------------------------------------------------------ #
    #  Unsupervised — clustering
    # ------------------------------------------------------------------ #
    "Clustering": _section(
        "Algorithm",
        "Unsupervised grouping. There is no ground truth — pick based on "
        "cluster shape, noise tolerance, and whether you need to specify k.",
        [
            ["K-Means",
             "Alternates between assigning each point to its nearest centroid and recomputing centroids as the mean of their assigned points, until assignments stop changing.",
             "Partition-based; minimizes within-cluster variance around centroids.",
             "Roughly spherical, similarly sized clusters; large n.",
             "Fast, simple, scales well.",
             "Must choose k; assumes spherical clusters; sensitive to initialization and outliers."],
            ["K-Medoids (PAM)",
             "Same alternating scheme as K-Means, but each cluster is represented by an actual data point (the medoid) that minimizes total dissimilarity.",
             "Like K-Means but centroids are actual data points (medoids).",
             "When you need interpretable medoids or robustness to outliers.",
             "Robust to outliers; medoids are real points.",
             "Slower than K-Means; still needs k."],
            ["Hierarchical (Agglomerative)",
             "Starts with each point as its own cluster and repeatedly merges the two closest clusters (or splits top-down), recording the merge order in a dendrogram.",
             "Bottom-up merges building a dendrogram.",
             "When you want a hierarchy or do not know k upfront.",
             "No need to specify k; dendrogram is interpretable.",
             "O(n²) memory and time; sensitive to linkage choice; irreversible merges."],
            ["DBSCAN",
             "Grows clusters from core points (at least min_samples neighbors within ε); points reachable from a core point join that cluster and everything else is labeled noise.",
             "Density-based; clusters are dense regions separated by sparse ones.",
             "Arbitrary-shaped clusters and noise / outlier detection.",
             "Finds arbitrary shapes, identifies noise, no k needed.",
             "Sensitive to eps and min_samples; struggles with varying density."],
            ["HDBSCAN",
             "Builds a hierarchy of density levels and keeps the clusters that persist across the widest range of densities.",
             "Hierarchical density-based variant of DBSCAN.",
             "Varying-density clusters and automatic cluster count.",
             "Handles varying density, robust, minimal tuning.",
             "Slower; less familiar; parameter sensitivity remains."],
            ["Gaussian Mixture Models",
             "Assumes the data come from a mixture of Gaussians and fits their parameters with EM: the E-step computes responsibilities, the M-step updates means and covariances.",
             "Probabilistic; models data as a mixture of Gaussians.",
             "Soft clustering, elliptical clusters, density estimation.",
             "Soft assignments; flexible covariance shapes.",
             "Assumes Gaussianity; can converge to bad local optima; needs k."],
            ["Spectral Clustering",
             "Builds a similarity graph, computes the Laplacian's eigenvectors, and clusters the points in that low-dimensional embedding with K-Means.",
             "Graph-based; clusters eigenvectors of a similarity matrix.",
             "Non-convex clusters; small-to-medium n.",
             "Captures complex shapes; no convexity assumption.",
             "O(n³) worst case; sensitive to the affinity matrix."],
            ["Mean Shift",
             "Each point climbs the gradient of the estimated density until it reaches a mode; points converging to the same mode form a cluster.",
             "Mode-seeking; points shift toward density peaks.",
             "When you do not know k and clusters are blob-like.",
             "No k needed; finds modes; robust.",
             "Slow on large data; bandwidth selection is critical."],
        ],
        with_how=True,
    ),

    # ------------------------------------------------------------------ #
    #  Unsupervised — dimensionality reduction
    # ------------------------------------------------------------------ #
    "Dim. Reduction": _section(
        "Method",
        "Compress features for visualization, denoising, or downstream "
        "modeling. Distinguish linear vs nonlinear and supervised vs unsupervised.",
        [
            ["PCA",
             "Computes the eigenvectors of the covariance matrix; projecting onto the top-k eigenvectors gives the k directions of greatest variance.",
             "Linear projection onto directions of maximum variance.",
             "Compression, decorrelation, visualization, denoising.",
             "Fast, deterministic, invertible, well-understood.",
             "Only captures linear structure; sensitive to scaling; components are less interpretable."],
            ["Kernel PCA",
             "Computes the kernel matrix, centers it, and solves an eigenproblem in that kernel-induced feature space — no explicit mapping needed.",
             "PCA in a kernel-induced feature space.",
             "Nonlinear structure that plain PCA misses.",
             "Captures nonlinearity; still a projection method.",
             "Kernel and hyperparameter choice; does not scale to large n."],
            ["t-SNE",
             "Builds per-point similarity distributions in high and low dimensions (Gaussians and t-distributions), then minimizes their KL divergence by gradient descent.",
             "Nonlinear; preserves local neighborhoods for visualization.",
             "Visualizing high-dimensional data in 2D or 3D.",
             "Excellent local structure; great for exploratory plots.",
             "Not for downstream modeling; stochastic; distances between clusters are not meaningful; slow."],
            ["UMAP",
             "Builds a fuzzy topological graph of the high-dimensional data and optimizes a low-dimensional layout whose fuzzy graph matches it as closely as possible.",
             "Nonlinear manifold learning; balances local and global structure.",
             "Visualization and preprocessing before clustering.",
             "Faster than t-SNE; preserves more global structure; scalable.",
             "Stochastic; hyperparameter-sensitive; theoretical guarantees weaker than PCA."],
            ["LDA (Linear Discriminant Analysis)",
             "Finds the projection that maximizes between-class scatter while minimizing within-class scatter — a generalized eigenproblem in those two scatter matrices.",
             "Supervised; maximizes between-class separation.",
             "Supervised dimensionality reduction for classification.",
             "Uses label information; interpretable; doubles as a classifier.",
             "Assumes Gaussian classes with shared covariance; at most C-1 components."],
            ["ICA",
             "Recovers statistically independent sources from mixed signals by maximizing the non-Gaussianity (or minimizing the mutual information) of the projections.",
             "Finds statistically independent components (not just uncorrelated).",
             "Blind source separation (EEG, audio, mixed signals).",
             "Recovers independent sources; stronger than uncorrelatedness.",
             "Assumes non-Gaussian independent sources; sign and scale ambiguity."],
            ["Autoencoders",
             "An encoder compresses the input into a bottleneck and a decoder reconstructs it; both are trained end to end to minimize reconstruction error.",
             "Neural bottleneck trained to reconstruct its input.",
             "Nonlinear compression, anomaly detection, representation learning.",
             "Learns nonlinear manifolds; flexible.",
             "Needs lots of data and tuning; latent space is not interpretable."],
        ],
        with_how=True,
    ),

    # ------------------------------------------------------------------ #
    #  Ensembles
    # ------------------------------------------------------------------ #
    "Ensembles": _section(
        "Method",
        "Combine models to reduce variance (bagging), reduce bias "
        "(boosting), or exploit model diversity (stacking).",
        [
            ["Bagging",
             "Trains the same model on B bootstrap samples and averages its predictions, which cancels much of the variance any single model carries.",
             "Parallel training on bootstrap samples; averages to reduce variance.",
             "High-variance base learners such as deep trees.",
             "Reduces variance; easy to parallelize.",
             "Does not reduce bias; less interpretable."],
            ["Boosting",
             "Trains models sequentially; each one targets the errors the ensemble still makes, so the combined model ends up with lower bias than any single one.",
             "Sequential training; each model corrects previous errors to reduce bias.",
             "High-bias base learners such as shallow trees.",
             "Reduces bias; typically top accuracy.",
             "Sequential; sensitive to noise and outliers; can overfit."],
            ["Stacking",
             "Trains several base models, collects their out-of-fold predictions, and fits a meta-model that learns how to combine them.",
             "Meta-model trained on out-of-fold predictions of base models.",
             "When different model families capture different signals.",
             "Exploits model diversity; can beat any single model.",
             "Complex; risk of leakage if folds are wrong; harder to maintain."],
            ["Voting",
             "Trains several models independently and combines their outputs by averaging class probabilities (soft) or taking the majority label (hard).",
             "Averages (soft) or majority-votes (hard) predictions of several models.",
             "Quick ensemble of diverse, comparable strong models.",
             "Simple, robust, easy to implement.",
             "Only helps if models are diverse and similarly strong."],
            ["Blending",
             "Like stacking, but the meta-model is trained on a single holdout set instead of out-of-fold predictions.",
             "Stacking with a holdout set instead of out-of-fold predictions.",
             "Simpler stacking alternative.",
             "Simpler to implement; less leakage risk.",
             "Wastes data on the holdout; less robust than CV-based stacking."],
        ],
        with_how=True,
    ),

    # ------------------------------------------------------------------ #
    #  Classification metrics
    # ------------------------------------------------------------------ #
    "Clf. Metrics": _section(
        "Metric",
        "Pick the metric that matches the business cost of FP vs FN. "
        "Accuracy is rarely the right default on imbalanced data.",
        [
            ["Accuracy",
             "Fraction of correct predictions.",
             "Balanced classes with equal misclassification costs.",
             "Intuitive; easy to explain.",
             "Misleading on imbalanced data."],
            ["Precision",
             "TP / (TP + FP): correctness of positive predictions.",
             "When false positives are costly (spam filters, fraud alerts).",
             "Directly optimizes for precision of positive calls.",
             "Ignores false negatives."],
            ["Recall / Sensitivity",
             "TP / (TP + FN): coverage of actual positives.",
             "When false negatives are costly (disease screening, fraud detection).",
             "Captures coverage of positives.",
             "Ignores false positives."],
            ["Specificity",
             "TN / (TN + FP): coverage of actual negatives.",
             "When false positives on negatives matter (benign recall).",
             "Complements recall.",
             "Ignores false negatives."],
            ["F1 Score",
             "Harmonic mean of precision and recall.",
             "Imbalanced data where both FP and FN matter.",
             "Balances precision and recall in a single number.",
             "Ignores true negatives; equal weighting of P and R may be wrong."],
            ["ROC-AUC",
             "Probability that a positive is ranked above a negative.",
             "Ranking problems; comparing models on balanced-ish data.",
             "Threshold-independent; interpretable.",
             "Optimistic on highly imbalanced data."],
            ["PR-AUC",
             "Area under the precision-recall curve.",
             "Highly imbalanced data; rare positives.",
             "Sensitive to the minority class.",
             "Less intuitive than ROC-AUC; depends on prevalence."],
            ["Log Loss",
             "Negative log-likelihood of the predicted probabilities.",
             "When you need calibrated probabilities.",
             "Penalizes confident wrong predictions; rewards calibration.",
             "Not a ranking metric; scale depends on class balance."],
            ["Brier Score",
             "Mean squared error of predicted probabilities.",
             "Calibration-focused evaluation.",
             "Bounded; decomposes into reliability and resolution.",
             "Less sensitive to ranking than AUC."],
            ["Matthews Correlation Coefficient",
             "Correlation between predicted and actual binary labels.",
             "Imbalanced binary classification; single balanced metric.",
             "Uses all four confusion-matrix cells; robust to imbalance.",
             "Harder to explain to stakeholders."],
            ["Cohen's Kappa",
             "Agreement between predictions and truth, corrected for chance.",
             "Multiclass or imbalanced settings where chance agreement matters.",
             "Chance-corrected.",
             "Can be unstable with rare classes."],
        ],
    ),

    # ------------------------------------------------------------------ #
    #  Regression metrics
    # ------------------------------------------------------------------ #
    "Reg. Metrics": _section(
        "Metric",
        "MAE is robust and interpretable; MSE/RMSE penalize large errors; "
        "R² is relative. Match the metric to the cost of errors.",
        [
            ["MAE",
             "Mean absolute error.",
             "When you want an interpretable average error in target units.",
             "Same units as target; robust to outliers.",
             "Not differentiable at zero; treats all errors linearly."],
            ["MSE",
             "Mean squared error.",
             "When large errors should be penalized more.",
             "Differentiable; smooth; standard for optimization.",
             "In squared units; very sensitive to outliers."],
            ["RMSE",
             "Square root of MSE.",
             "When you want error in target units but still penalize large errors.",
             "Same units as target; penalizes large errors.",
             "Still sensitive to outliers; scale-dependent."],
            ["MAPE",
             "Mean absolute percentage error.",
             "When relative error matters and the target is strictly positive.",
             "Scale-free; interpretable as a percentage.",
             "Undefined or explosive near zero; asymmetric."],
            ["sMAPE",
             "Symmetric version of MAPE.",
             "Forecasting with mixed scales.",
             "Bounded; symmetric.",
             "Still undefined at zero; not a true percentage."],
            ["R²",
             "Proportion of variance explained.",
             "Comparing models on the same data.",
             "Scale-free; intuitive.",
             "Can be negative; does not measure absolute fit."],
            ["Adjusted R²",
             "R² penalized for the number of predictors.",
             "Comparing models with different feature counts.",
             "Penalizes overfitting.",
             "Still relative; only comparable on the same target."],
            ["Quantile / Pinball Loss",
             "Loss for a specific quantile prediction.",
             "Probabilistic forecasting; asymmetric costs.",
             "Captures tail behavior; flexible.",
             "Less familiar; one model per quantile."],
            ["Huber Loss",
             "Quadratic for small errors, linear for large ones.",
             "When you want outlier robustness with smooth gradients.",
             "Combines MAE and MSE strengths; differentiable.",
             "One more hyperparameter (delta) to tune."],
        ],
    ),

    # ------------------------------------------------------------------ #
    #  Validation
    # ------------------------------------------------------------------ #
    "Validation": _section(
        "Method",
        "Estimate generalization performance. The split must mirror how "
        "the model will be used in production.",
        [
            ["Hold-out",
             "Single train / validation / test split.",
             "Very large data, or fast iteration.",
             "Fast, simple, no leakage if the split is correct.",
             "High variance; wastes data; can be unlucky."],
            ["K-Fold CV",
             "Rotating validation across k folds.",
             "General-purpose model selection.",
             "Lower-variance estimate; uses all data.",
             "k-fold training cost; can leak if preprocessing is done outside folds."],
            ["Stratified K-Fold",
             "K-Fold that preserves class proportions in each fold.",
             "Classification, especially imbalanced.",
             "Stable class ratios; better estimates.",
             "Only for classification; still k-fold cost."],
            ["Leave-One-Out (LOO)",
             "K-Fold with k equal to n.",
             "Very small datasets.",
             "Uses almost all data; low bias.",
             "High variance; n-fold training cost; can be pessimistic."],
            ["Group K-Fold",
             "Folds split by group (user, patient, ...), not row.",
             "When rows from the same entity would otherwise leak across folds.",
             "Prevents group leakage; realistic estimates.",
             "Requires a group column; can be imbalanced."],
            ["Time Series Split",
             "Expanding or sliding window respecting time order.",
             "Temporal data.",
             "Respects chronology; no future leakage.",
             "Fewer validation points; early folds are small."],
            ["Nested CV",
             "Outer loop for evaluation, inner loop for hyperparameter tuning.",
             "Unbiased performance estimate when tuning is involved.",
             "Separates tuning from evaluation; low bias.",
             "k_outer times k_inner times training cost."],
            ["Bootstrap",
             "Resample with replacement; evaluate on out-of-bag samples.",
             "Small data, confidence intervals, bagging.",
             "Gives uncertainty estimates; flexible.",
             "Overlapping train and validation; optimistic if not careful."],
        ],
    ),

    # ------------------------------------------------------------------ #
    #  Imbalanced data
    # ------------------------------------------------------------------ #
    "Imbalanced Data": _section(
        "Technique",
        "Standard classifiers optimize accuracy and ignore the minority "
        "class. These techniques rebalance the learning signal or the decision rule.",
        [
            ["Class weights",
             "Re-weights the loss to penalize minority errors more.",
             "Any classifier that supports sample weights.",
             "No data change; simple; often effective.",
             "Requires model support; can destabilize training."],
            ["Random oversampling",
             "Duplicate minority samples.",
             "Quick baseline.",
             "Simple; no information loss.",
             "Overfitting on duplicated points."],
            ["Random undersampling",
             "Drop majority samples.",
             "Very large majority class.",
             "Fast; reduces imbalance.",
             "Throws away information; can increase variance."],
            ["SMOTE",
             "Synthesize minority points along segments between neighbors.",
             "Moderate imbalance with continuous features.",
             "Adds diversity; often better than duplication.",
             "Can create noisy or implausible points; poor fit for categorical features."],
            ["ADASYN",
             "SMOTE variant focusing on hard-to-classify minority points.",
             "When some minority regions are harder than others.",
             "Adaptive; targets the boundary.",
             "Noisy; sensitive to neighbor choice."],
            ["Threshold tuning",
             "Move the decision threshold to trade precision vs recall.",
             "When you care about a specific operating point.",
             "No retraining; directly optimizes the metric you care about.",
             "Changes only the operating point, not the model's ranking."],
            ["Cost-sensitive learning",
             "Assign explicit misclassification costs.",
             "When FP and FN have known, different costs.",
             "Directly aligns with business costs.",
             "Needs cost estimates; not all models support it."],
            ["Anomaly detection framing",
             "Treat the minority class as anomalies (Isolation Forest, One-Class SVM).",
             "Extreme imbalance (fraud, defects).",
             "Designed for rare events; no need for balanced labels.",
             "Different evaluation paradigm; harder to compare with classifiers."],
        ],
    ),

    # ------------------------------------------------------------------ #
    #  Feature selection
    # ------------------------------------------------------------------ #
    "Feature Selection": _section(
        "Method",
        "Fewer features means faster, less overfitting, and easier "
        "interpretation. Filter methods are fast but ignore interactions; "
        "embedded and wrapper methods are model-aware.",
        [
            ["Variance threshold",
             "Drop near-zero-variance features.",
             "Preprocessing cleanup.",
             "Trivial and fast.",
             "Only removes constant or near-constant features."],
            ["Correlation filter",
             "Drop highly correlated features.",
             "Multicollinearity cleanup.",
             "Fast; improves linear model stability.",
             "Ignores the target; pairwise only."],
            ["Univariate tests (chi-square, ANOVA F, mutual information)",
             "Score each feature against the target independently.",
             "Quick screening before modeling.",
             "Fast, model-agnostic, interpretable.",
             "Ignores interactions; may drop features that only matter jointly."],
            ["Recursive Feature Elimination (RFE)",
             "Iteratively fit a model and remove the weakest feature.",
             "When you have a decent model and want a subset.",
             "Model-aware; considers interactions.",
             "Expensive (many fits); greedy."],
            ["L1 / Lasso",
             "Shrink coefficients to zero via an L1 penalty.",
             "Linear models with many features.",
             "Embedded in training; sparse solution.",
             "Only for linear models; unstable with correlated features."],
            ["Tree-based importance",
             "Uses impurity decrease or permutation importance.",
             "Tree ensembles.",
             "Captures nonlinearity and interactions.",
             "Impurity importance is biased toward high-cardinality features; permutation importance is sensitive to correlated features."],
            ["Boruta",
             "Compares feature importance against shuffled shadow features.",
             "When you want a robust all-relevant feature set.",
             "Statistically grounded; handles interactions.",
             "Slower; depends on a tree model."],
            ["Permutation importance",
             "Measures the drop in performance when a feature is shuffled.",
             "Model-agnostic post-hoc interpretation.",
             "Model-agnostic; measures actual predictive contribution.",
             "Can mislead with correlated features; needs a validation set."],
        ],
    ),
        # ------------------------------------------------------------------ #
    #  Exploratory data analysis
    # ------------------------------------------------------------------ #
    "EDA": {
        "description": (
            "Explore the data before modelling. Each step builds on the "
            "previous one — skip the early audits and every downstream "
            "metric, group-by and model becomes unreliable. Treat this as "
            "a checklist, not a linear script: findings from later steps "
            "often send you back to earlier ones."
        ),
        "columns": [
            "Step",
            "How to do it",
            "Main components to check",
            "Why it matters",
            "Common pitfalls and red flags",
        ],
        "widths": ["12%", "22%", "22%", "20%", "24%"],
        "rows": [
            [
                "Data inventory and schema audit",
                "Start with df.shape, df.info(), df.dtypes, df.head() and "
                "df.sample(5). Cross-check against the data dictionary. "
                "Write down what one row represents (the grain) before "
                "touching anything else.",
                "Column names and dtypes, row count versus expectation, "
                "memory footprint, ID and timestamp columns, units of every "
                "numeric column, string-encoded numbers or dates.",
                "Wrong grain or misread dtypes silently corrupt every "
                "downstream step. A date read as a string cannot be plotted "
                "over time; a numeric read as an object cannot be scaled or "
                "averaged.",
                "Numeric-looking strings like 1,234 or 12.5%, dates loaded "
                "as object, mixed dtypes inside a column, unexpected columns "
                "such as a hidden label.",
            ],
            [
                "Data quality audit (missing, duplicates, invalid)",
                "df.isna().sum() and df.isna().mean(); a missingness "
                "heatmap (sns.heatmap(df.isna())). df.duplicated().sum() "
                "and duplicate checks on ID-like keys. Range and regex checks "
                "on every column.",
                "Missing per column and co-missing patterns, duplicate rows "
                "or duplicate keys, invalid values (negative prices, "
                "impossible ages), inconsistent category spellings.",
                "Metrics, group-bys and models silently produce wrong "
                "answers on dirty data. The missingness mechanism (MCAR, "
                "MAR, MNAR) determines whether imputation is safe.",
                "Dropping rows without understanding why they are missing, "
                "imputing before splitting the data (leaks validation info), "
                "treating placeholder strings like N/A, unknown or -1 as "
                "real categories.",
            ],
            [
                "Univariate analysis — numeric",
                "df.describe(percentiles=[.01, .25, .5, .75, .99]), "
                "histograms and KDEs (sns.histplot, sns.kdeplot), boxplots, "
                "df.skew() and df.kurtosis().",
                "Center (mean versus median), spread (std, IQR), shape "
                "(skew, multimodality), hard bounds, tail behaviour.",
                "Guides scaling choice, transformations (log, Box-Cox) and "
                "whether mean-based statistics are meaningful. Heavy tails "
                "and multimodality often reveal a hidden subgroup.",
                "Mean and std on heavily skewed data mislead; multimodal "
                "distributions hiding a categorical subgroup; mistaking a "
                "hard cap (age 99) for the real max.",
            ],
            [
                "Univariate analysis — categorical",
                "df[col].value_counts() and value_counts(normalize=True); "
                "df[col].nunique(); bar charts sorted by frequency.",
                "Frequency distribution, cardinality, dominant category, "
                "rare levels, ambiguous category labels.",
                "Determines encoding strategy (one-hot, target, frequency, "
                "embedding) and warns about rare or unseen categories in "
                "production.",
                "High cardinality (hundreds of levels) blows up one-hot and "
                "leaks through target encoding; a near-constant column (99% "
                "one value) adds noise, not signal.",
            ],
            [
                "Outlier and anomaly inspection",
                "Boxplots per numeric column, IQR rule (outside Q1 - "
                "1.5*IQR or Q3 + 1.5*IQR), z-scores, scatter plots. Inspect "
                "each flagged row individually, not just the count.",
                "Extreme values, whether they are isolated or clustered, "
                "business plausibility (is a 100k order real?), co-occurrence "
                "of extremes across columns.",
                "Separates business-critical signal (fraud, churn, disease) "
                "from data errors that should be clipped or dropped. Both "
                "kinds affect fitting, but they call for opposite responses.",
                "Blindly clipping removes real signal; treating a statistical "
                "outlier as an error without a domain check; fixing in the "
                "notebook but not in the production pipeline.",
            ],
            [
                "Bivariate — numeric versus numeric",
                "df.corr() with a heatmap (sns.heatmap), sns.pairplot, "
                "scatterplots, Spearman next to Pearson, VIF for "
                "collinearity.",
                "Pearson and Spearman correlations, collinearity clusters, "
                "non-linear relationships masked by Pearson, near-perfect "
                "correlations.",
                "Collinearity destabilises linear models; strong correlations "
                "often point to leakage or redundant features; non-linear "
                "relations guide transformations and feature crosses.",
                "Pearson only catches linear relations; correlations on "
                "skewed or ordinal data mislead; ignoring the difference "
                "between correlated and causally related.",
            ],
            [
                "Bivariate — feature versus target",
                "Boxplots of numerics grouped by target, mean target rate "
                "per bin for continuous features, target rate per category, "
                "mutual information, effect size (Cohen's d, odds ratio).",
                "Effect size and direction, monotonicity, non-linear shapes "
                "(U-shaped, thresholded), subgroup variance.",
                "Tells you which features are worth keeping, whether "
                "relationships are linear and whether categoricals need "
                "grouping. Effect size beats p-values on large datasets.",
                "Simpson's paradox — a marginal effect reverses when a group "
                "is conditioned on; p-values on huge samples flag trivial "
                "effects; computing target statistics outside "
                "cross-validation leaks.",
            ],
            [
                "Multivariate analysis and interactions",
                "Pairwise plots coloured by target, 2D density "
                "(sns.kdeplot with fill=True), conditional means "
                "(groupby two columns then describe), pd.crosstab for two "
                "categoricals against the target.",
                "Interactions (feature A's effect depends on feature B), "
                "distinct segments, subgroup-specific patterns, clusters "
                "visible only in higher dimensions.",
                "Linear models cannot see interactions; trees can but need "
                "enough data. Interaction discovery guides feature "
                "engineering and, in consulting, segment-specific "
                "recommendations.",
                "Over-interpreting conditional means on small subgroups, "
                "ignoring confounders, spurious interactions when many "
                "features are crossed with few samples.",
            ],
            [
                "Temporal and structural checks",
                "Line plots of aggregates over time "
                "(df.groupby(pd.Grouper(key='date', freq='W')).size()), "
                "autocorrelation plots, seasonality decomposition, compare "
                "train versus production feature distributions.",
                "Trends, seasonality, level shifts, weekly or monthly "
                "cycles, covariate shift between train and test or "
                "production.",
                "Time-correlated features need time-based validation, not "
                "random splits. Drift between training and production is "
                "the most common cause of silent production degradation.",
                "Random train/test split on time-series data leaks future "
                "into past; comparing only marginal distributions misses "
                "joint shift; ignoring as-of correctness of features.",
            ],
            [
                "Leakage and train/test consistency audit",
                "Search for suspiciously high feature importance or "
                "correlation with the target; scan column names for "
                "after-the-fact hints (closed_at, churn_reason, "
                "refund_date); compare feature distributions across train, "
                "validation and test; verify each feature is available at "
                "prediction time.",
                "ID-like columns, near-perfect predictors, future-dated "
                "features, distributions that differ between train and "
                "test, features that update after the target event.",
                "Leakage inflates validation scores and collapses in "
                "production — the most expensive bug to catch after the "
                "fact, because the model looks great until it does not.",
                "Dropping a leakage feature without confirming the source; "
                "using a random split when the data has temporal structure; "
                "not checking whether a feature is populated at the same "
                "time as the prediction.",
            ],
            [
                "EDA summary and documentation",
                "Write findings in a dedicated section of the notebook or a "
                "short memo. Maintain a data dictionary, a transformation "
                "log (what was dropped and why) and a list of open "
                "questions.",
                "Data dictionary, quality-issue register and its resolution, "
                "feature list with transform decisions, hypotheses and "
                "risks to test in modelling, open questions for the "
                "business.",
                "EDA findings drive every modelling decision. Undocumented, "
                "they get re-litigated or forgotten and the same mistakes "
                "repeat.",
                "EDA stays only in the analyst's head; features are dropped "
                "without a recorded reason; EDA conclusions are never "
                "linked back to modelling choices.",
            ],
        ],
    },
        # ------------------------------------------------------------------ #
    #  Data and AI business use cases
    # ------------------------------------------------------------------ #
    "Business Use Cases": {
        "description": (
            "The recurring Data and AI use cases in consulting work. Each row "
            "is a scoping sheet: what the client asks for, how to frame it, "
            "which KPIs to promise, what data you need, which modelling "
            "family to reach for, and the recommendations you will actually "
            "put in the readout. Use it as a first-meeting checklist rather "
            "than a blueprint — every project reshapes the middle columns."
        ),
        "columns": [
            "Use case",
            "Industries",
            "First questions to ask",
            "Main KPIs",
            "Where to source data",
            "Approach to take",
            "Recommendations to make",
        ],
        "widths": ["9%", "10%", "15%", "13%", "14%", "19%", "20%"],
        "rows": [
            [
                "Churn prediction",
                "Telecom, subscription SaaS, retail, banking, energy",
                "How is churn defined (contract end, inactivity window)? What "
                "is the prediction horizon? What action will the business "
                "take on a churner, and what does it cost versus a lost "
                "customer?",
                "Churn rate, retention rate, save rate, precision at the "
                "campaign capacity, incremental retained revenue, ARPU.",
                "CRM (contracts, tickets), product telemetry, billing and "
                "payment history, support tickets, NPS and surveys, "
                "marketing engagement.",
                "Binary classifier (gradient boosting baseline) on a "
                "carefully defined churn window; time-based splits; class "
                "weights and threshold tuning; survival analysis if the "
                "timing matters; rank by expected saved revenue, not raw "
                "probability.",
                "Rank the retention queue by expected saved revenue, not "
                "probability, and size it to the retention team's real "
                "capacity. A/B test the offer. Instrument drift monitoring "
                "and feed the score into the CS workflow.",
            ],
            [
                "Fraud detection",
                "Banking, payments, insurance, e-commerce, telecom",
                "What is the label (chargeback, investigation outcome, "
                "confirmed fraud)? What is the detection latency requirement "
                "(real-time vs batch)? What is the cost of a false positive "
                "versus a false negative?",
                "Fraud loss rate, precision and recall at the operating "
                "threshold, alert volume per analyst, time-to-detect, "
                "chargeback rate, recovery rate.",
                "Transaction logs, device and session data, KYC and user "
                "profiles, historical investigation labels, merchant data, "
                "fraud consortium sharing.",
                "Imbalanced classification evaluated on PR-AUC, not "
                "ROC-AUC; layered rules plus a model; real-time scoring "
                "with a feature store; threshold set from the cost matrix; "
                "concept-drift monitoring.",
                "Combine rules with ML for explainability and early wins. "
                "Operate at the analysts' alert capacity. Retrain often and "
                "track precision at fixed alert volume, not just AUC.",
            ],
            [
                "Customer segmentation",
                "Retail, marketing, telecom, banking, FMCG",
                "What decisions will the segmentation drive? Which "
                "behavioural dimensions matter (RFM, engagement, value)? How "
                "many segments can the business actually activate?",
                "Segment size and stability, revenue and retention per "
                "segment, campaign lift per segment, share of segments that "
                "are actually targeted.",
                "Transaction history, CRM, product usage, web and app "
                "analytics, survey data, third-party demographic enrichment.",
                "Start with RFM for interpretability, then K-Means or GMM "
                "on scaled behavioural features, or hierarchical clustering "
                "when the hierarchy matters; validate stability across "
                "months; name segments in business language.",
                "Cap the number of segments at what the business can "
                "action (3-8, not 20). Name them by behaviour, not cluster "
                "number, and re-run periodically to track drift.",
            ],
            [
                "Recommendation and personalisation",
                "Retail, media and streaming, travel, marketing, e-commerce",
                "Which interactions exist (implicit vs explicit) and how "
                "dense are they? How should cold start be handled? Is the "
                "objective engagement, conversion or revenue? What are the "
                "latency constraints?",
                "CTR, conversion rate, AOV, revenue per user, catalogue "
                "coverage and diversity, cold-start rate, retention.",
                "Interaction logs (views, clicks, purchases), product "
                "catalogue and metadata, user profiles, session events, "
                "past A/B test results.",
                "Baseline popularity or co-occurrence, then matrix "
                "factorisation, then two-tower or sequence models; hybrid "
                "content-based signals for cold start; rank by expected "
                "utility; always ship behind an A/B test.",
                "Measure long-term retention, not just CTR. Add diversity "
                "and freshness constraints to avoid filter bubbles. Seed "
                "cold start with content and demographic signals.",
            ],
            [
                "CLV prediction",
                "Retail, telecom, banking, subscription SaaS, marketing",
                "Is CLV a customer-level prediction or a segment average? "
                "What is the horizon (12 months, 3 years, lifetime)? Are "
                "margin and churn data available at transaction granularity?",
                "Predicted versus realised CLV, margin-adjusted CLV, "
                "CLV-to-CAC ratio, CAC payback period, top-decile CLV "
                "concentration.",
                "Transaction and billing history, churn events, margin "
                "data, acquisition cost by channel, engagement telemetry.",
                "Two-stage (churn x revenue) or direct regression on "
                "lifetime value; survival models for time-to-churn; BG/NBD "
                "for non-contractual businesses; rank customers by CLV.",
                "Segment by CLV rather than recency, allocate acquisition "
                "budget by CLV/CAC by channel, and feed high-value "
                "predictions into retention. Caveat long-horizon "
                "predictions explicitly.",
            ],
            [
                "Demand forecasting",
                "Retail, FMCG, supply chain, energy, hospitality",
                "What is the forecast granularity (SKU x store x day) and "
                "horizon? Is the forecast for inventory or staffing? What is "
                "the cost of over- versus under-forecasting?",
                "MAPE or sMAPE or MASE, bias, forecast value added over a "
                "naive baseline, stockout rate, overstock or obsolescence, "
                "service level (fill rate).",
                "Historical sales, promotions and calendar, pricing, "
                "inventory position, weather, macro indicators, web search "
                "trends.",
                "Baseline (naive, seasonal naive), exponential smoothing, "
                "then gradient boosting or deep sequence models with "
                "calendar and exogenous features; hierarchical "
                "reconciliation; quantile forecasts for safety stock.",
                "Always beat the naive baseline before showing anything "
                "else. Forecast quantiles, not just the mean. Backtest on "
                "time, never random CV. Reconcile hierarchical forecasts "
                "and monitor bias separately from error.",
            ],
            [
                "Dynamic pricing",
                "Retail, travel, ride-hailing, energy, e-commerce",
                "Is price elasticity known or must it be estimated? What "
                "are the constraints (fairness, regulation, competitor "
                "parity, cost floor)? Is the objective revenue, margin or "
                "volume?",
                "Revenue, gross margin, conversion rate, price realisation, "
                "elasticity estimate, competitive price index, long-term "
                "price sensitivity.",
                "Historical price and volume, competitor price scrapes, "
                "promotion history, demand signals, cost data, "
                "willingness-to-pay surveys.",
                "Causal estimation first (A/B pricing tests, "
                "difference-in-differences) to get elasticity, then an "
                "optimisation layer (regression plus constraint solver); "
                "only consider reinforcement learning once the causal "
                "baseline holds.",
                "Estimate elasticity causally before optimising, set "
                "guardrails (margin floor, fairness constraints), A/B test "
                "price changes on a small share, and monitor long-term "
                "price perception, not just quarterly revenue.",
            ],
            [
                "Credit and risk scoring",
                "Banking, insurance, fintech, utilities",
                "What is the outcome definition (default, delinquency 30 "
                "days, claim)? What is the regulatory regime for "
                "explainability and adverse-action reasons? Are protected "
                "attributes excluded by law?",
                "AUC and KS and Gini, population stability index (PSI), "
                "approval rate, default rate, expected loss, bad rate by "
                "score band, fairness metrics across groups.",
                "Application data, credit bureau reports, transaction "
                "history, KYC and AML data, alternative data (utility, "
                "telco, open banking).",
                "Logistic regression is often preferred for "
                "interpretability; gradient boosting with SHAP when "
                "explainability is satisfied; scorecard-style banding; "
                "probability calibration; monthly PSI monitoring; fairness "
                "audit.",
                "Choose model complexity subject to explainability rules, "
                "document adverse-action reasons per score band, "
                "recalibrate as the population drifts, and run a fairness "
                "audit before go-live.",
            ],
            [
                "Lead scoring",
                "SaaS, professional services, industrial B2B, marketing",
                "What is the conversion event (SQL, demo booked, "
                "closed-won)? How are leads captured and attributed? What "
                "is the sales team's capacity for follow-up?",
                "Conversion rate by score band, precision at top-k, "
                "sales-accepted lead rate, cost per qualified lead, close "
                "rate, sales cycle length.",
                "CRM (leads, opportunities, activities), marketing "
                "automation, web and product engagement, firmographic "
                "enrichment, email engagement, call logs.",
                "Binary classifier on the conversion event, evaluated as a "
                "ranking problem; combine a fit score (firmographic) with "
                "an intent score (recent engagement); account-level "
                "aggregation for B2B.",
                "Combine fit and intent, set the top-k cut-off to sales "
                "capacity, feed scores into the CRM, and evaluate by "
                "precision at that cut-off rather than overall AUC.",
            ],
            [
                "Uplift and next-best-action",
                "Telecom, retail, banking, insurance, marketing",
                "Is there randomised treatment data (past campaigns with a "
                "control arm)? What are the available actions (discount, "
                "call, email) and their costs? What constraints apply?",
                "Incremental conversion, uplift at k, Qini coefficient, "
                "cost per incremental conversion, campaign ROI, persuadable "
                "share.",
                "Past campaign data with treatment and control assignment, "
                "customer covariates, contact history, outcome data.",
                "Two-model (treatment vs control), causal forest, or "
                "X-/R-learner; requires experimental data to identify "
                "uplift; A/B test the deployed policy, not just the model.",
                "Do not attempt uplift without experimental data — "
                "observational propensity modelling answers a different "
                "question. Rank by incremental effect, A/B test the policy, "
                "and watch for treatment fatigue.",
            ],
            [
                "Predictive maintenance",
                "Manufacturing, energy, transportation, facilities",
                "What counts as a failure (unplanned downtime, part "
                "replacement)? What sensors exist and at what frequency? "
                "What is the cost of a false alarm versus a missed failure?",
                "Downtime hours, MTBF, MTTR, precision and recall on "
                "failure events, lead time to failure, maintenance cost per "
                "unit, false alarm rate.",
                "IoT time series (vibration, temperature, current), "
                "maintenance logs, failure records, equipment metadata, "
                "ERP and MES systems.",
                "Anomaly detection plus remaining-useful-life prediction; "
                "survival or sequence models; careful labelling of rare "
                "failure events with lead time; align alerts with the "
                "maintenance schedule.",
                "Predict remaining useful life rather than a raw failure "
                "probability, align alerts with the maintenance planning "
                "cadence, and control false alarms actively — trust in the "
                "system collapses after a few noisy alerts.",
            ],
            [
                "GenAI assistant (RAG)",
                "Professional services, banking, healthcare, legal, "
                "customer service, marketing",
                "What is the corpus and how often does it change? Must "
                "every answer cite a source? Is a hallucination acceptable "
                "for this use case? What compliance and data-residency "
                "constraints apply?",
                "Answer accuracy, groundedness and faithfulness, citation "
                "correctness, hallucination rate, p50 and p95 latency, cost "
                "per query, deflection rate, user satisfaction.",
                "Internal document stores (SharePoint, Confluence, drive), "
                "structured databases, support tickets, FAQs, policy and "
                "knowledge-base documents.",
                "Retrieval-augmented generation with a strong prompt first; "
                "careful chunking, embeddings and reranking; grounding "
                "checks; human-in-the-loop for high-stakes answers; "
                "evaluate against a labelled question set with "
                "RAG-specific metrics.",
                "Start with retrieval before fine-tuning, force citations, "
                "add a confidence fallback (an explicit I do not know), "
                "and build the evaluation set before deployment. Monitor "
                "for drift in both corpus and queries.",
            ],
        ],
    },
}
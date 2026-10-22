"""Statistics playbook: t-tests and A/B tests.

Focus: 1- and 2-sided t-tests (one-sample, paired, two-sample) and the
A/B testing framework built on top of them. Every card shows the same
three mathematical objects — estimator, confidence interval, hypothesis
test — so the reader sees the common skeleton across every variant.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MathBlock:
    label: str
    math: str    # raw LaTeX — fed straight to st.latex
    note: str    # markdown — a short interpretation


@dataclass(frozen=True)
class StatCard:
    id: str
    name: str
    tagline: str
    intro: str
    math_blocks: tuple[MathBlock, ...]
    assumptions: tuple[str, ...]
    advantages: tuple[str, ...]
    disadvantages: tuple[str, ...]
    code: str = ""


# --------------------------------------------------------------------------- #
#  Card 1 — One-sample t-test
# --------------------------------------------------------------------------- #
_ONE_SAMPLE = StatCard(
    id="one_sample",
    name="One-sample t-test",
    tagline="Compare a sample mean to a benchmark — the base case every other t-test is built from.",
    intro=(
        "Given a sample from a population with unknown mean and unknown "
        "variance, we ask whether the mean equals a reference value. Every "
        "subsequent card reuses the same three objects (estimator, CI, test) "
        "with a different estimator. The paired t-test is just this card "
        "applied to the per-pair differences."
    ),
    math_blocks=(
        MathBlock(
            label="Estimator and standard error",
            math=r"""
\bar{x} = \frac{1}{n} \sum_{i=1}^n x_i,
\qquad
\mathrm{SE}(\bar{x}) = \frac{s}{\sqrt{n}}
""",
            note=(
                "The sample mean is **unbiased** for μ with variance σ²/n. "
                "Since σ is unknown we plug in the sample SD s — that "
                "substitution is exactly why the test below uses a "
                "t-distribution rather than a normal. The SE shrinks as "
                "1/√n: quadrupling the sample halves the SE."
            ),
        ),
        MathBlock(
            label="Test statistic and sampling distribution",
            math=r"""
t = \frac{\bar{x} - \mu_0}{s / \sqrt{n}}
\;\;\sim\;\; t_{n-1} \quad \text{under } H_0
""",
            note=(
                "The t-distribution is fatter-tailed than normal and converges "
                "to normal as n grows. For n ≥ 30 the difference is small; "
                "for n < 15 it matters."
            ),
        ),
        MathBlock(
            label="Two-sided confidence interval",
            math=r"""
\left[\;
\bar{x} - t_{\alpha/2,\,n-1} \cdot \frac{s}{\sqrt{n}},
\quad
\bar{x} + t_{\alpha/2,\,n-1} \cdot \frac{s}{\sqrt{n}}
\;\right]
""",
            note=(
                "Values inside the interval are plausible values of μ at "
                "confidence level 1−α. **CI ↔ test duality:** a two-sided test "
                "rejects H₀: μ = μ₀ at level α iff the corresponding "
                "(1−α) two-sided CI excludes μ₀. Same calculation, two views."
            ),
        ),
        MathBlock(
            label="Two-sided hypothesis test",
            math=r"""
H_0: \mu = \mu_0,
\qquad
H_1: \mu \neq \mu_0,
\qquad
p = 2 \cdot P\left(T_{n-1} > |t|\right)
""",
            note=(
                "Reject H₀ iff p < α, equivalently iff |t| > t_{α/2,n−1}. The "
                "factor of 2 is the two-sided signature — α is split across "
                "both tails, so each tail gets α/2."
            ),
        ),
        MathBlock(
            label="One-sided variants",
            math=r"""
\begin{aligned}
& H_1: \mu > \mu_0
\;\Longrightarrow\;
p = P(T_{n-1} > t), \quad
\mathrm{CI} = \left[\bar{x} - t_{\alpha,n-1}\cdot\frac{s}{\sqrt{n}},\; +\infty\right)
\\[4pt]
& H_1: \mu < \mu_0
\;\Longrightarrow\;
p = P(T_{n-1} < t), \quad
\mathrm{CI} = \left(-\infty,\; \bar{x} + t_{\alpha,n-1}\cdot\frac{s}{\sqrt{n}}\right]
\end{aligned}
""",
            note=(
                "A one-sided CI is a **half-line** — it bounds μ on one side "
                "only. That's the trade: more power to detect a deviation in "
                "the chosen direction, but zero coverage in the other. See "
                "the *One-sided vs two-sided* card for when each is "
                "defensible."
            ),
        ),
        MathBlock(
            label="Paired t-test — a one-sample test on differences",
            math=r"""
d_i = y_i^{\text{after}} - y_i^{\text{before}},
\qquad
t = \frac{\bar{d}}{s_d / \sqrt{n}} \sim t_{n-1}
""",
            note=(
                "Pairing removes between-subject variance, which is why the "
                "paired test has far more power than an independent two-sample "
                "test on the same n — provided the pairing is real. Random "
                "pairing gains nothing and can even hurt."
            ),
        ),
    ),
    assumptions=(
        "Observations are independent — or, for paired data, the pairs "
        "themselves are independent.",
        "The sample mean is approximately normal: **exact** if the data are "
        "normal, adequate by the central limit theorem for roughly n ≥ 30.",
        "The variable is continuous, or discrete enough to be treated as "
        "continuous.",
    ),
    advantages=(
        "Exact for normal data; closed-form critical values and CI.",
        "Point estimate, CI and p-value all come out of the same "
        "calculation — no additional work.",
        "Generalises cleanly to paired and two-sample cases.",
    ),
    disadvantages=(
        "Sensitive to outliers — one extreme point can move the mean far.",
        "Assumes normality for small samples; use a Wilcoxon or bootstrap "
        "fallback if the QQ-plot fails.",
        "Only about the mean, not the median or the shape of the "
        "distribution.",
    ),
    code="""from scipy import stats

# Two-sided
stats.ttest_1samp(x, popmean=mu0)

# One-sided (H1: mu > mu0)
stats.ttest_1samp(x, popmean=mu0, alternative='greater')

# Paired
stats.ttest_rel(before, after)""",
)


# --------------------------------------------------------------------------- #
#  Card 2 — Two-sample t-test
# --------------------------------------------------------------------------- #
_TWO_SAMPLE = StatCard(
    id="two_sample",
    name="Two-sample t-test",
    tagline="Compare the means of two independent groups — the workhorse of A/B testing on continuous metrics.",
    intro=(
        "Two samples drawn independently from two populations; ask whether "
        "their means differ. Same three objects as the one-sample case, but "
        "the estimator is now the **difference in means** and the SE has to "
        "account for variance in both arms. The only real choice is Welch "
        "versus Student — and modern practice defaults to Welch."
    ),
    math_blocks=(
        MathBlock(
            label="Estimator",
            math=r"""
\hat{\delta} = \bar{x}_1 - \bar{x}_2,
\qquad
\mathbb{E}[\hat{\delta}] = \mu_1 - \mu_2,
\qquad
\mathrm{Var}(\hat{\delta}) = \frac{\sigma_1^2}{n_1} + \frac{\sigma_2^2}{n_2}
""",
            note=(
                "The natural point estimate is unbiased, and its variance is "
                "the sum of the two per-arm variances — provided the two "
                "samples really are independent. Violating independence "
                "(network effects, clustered users) breaks this formula and "
                "usually understates the SE."
            ),
        ),
        MathBlock(
            label="Standard error — Welch (default)",
            math=r"""
\mathrm{SE}_{\text{Welch}} = \sqrt{\frac{s_1^2}{n_1} + \frac{s_2^2}{n_2}}
""",
            note=(
                "Each group's variance enters on its own — no pooling. This "
                "is the modern default: it stays valid under unequal "
                "variances **and** unequal arm sizes, which is the realistic "
                "case in production A/B tests."
            ),
        ),
        MathBlock(
            label="Standard error — Student (pooled)",
            math=r"""
s_p^2 = \frac{(n_1-1)s_1^2 + (n_2-1)s_2^2}{n_1 + n_2 - 2},
\qquad
\mathrm{SE}_{\text{Student}} = s_p \sqrt{\frac{1}{n_1} + \frac{1}{n_2}}
""",
            note=(
                "Assumes σ₁ = σ₂ and borrows strength from both arms via the "
                "pooled estimate. Slightly more powerful than Welch **if** the "
                "assumption holds — noticeably less reliable when it doesn't. "
                "Only reach for Student if you're confident variances match."
            ),
        ),
        MathBlock(
            label="Test statistic and degrees of freedom",
            math=r"""
\begin{aligned}
\text{Welch:}\quad & t = \frac{\hat{\delta}}{\mathrm{SE}_{\text{Welch}}},
\quad
\mathrm{df} =
\frac{\left(\frac{s_1^2}{n_1} + \frac{s_2^2}{n_2}\right)^2}
     {\frac{(s_1^2/n_1)^2}{n_1-1} + \frac{(s_2^2/n_2)^2}{n_2-1}} \\[6pt]
\text{Student:}\quad & t = \frac{\hat{\delta}}{\mathrm{SE}_{\text{Student}}},
\quad
\mathrm{df} = n_1 + n_2 - 2
\end{aligned}
""",
            note=(
                "Welch's degrees of freedom is fractional (Satterthwaite's "
                "approximation) — don't be surprised by df = 84.7. It reflects "
                "that Welch is trading off against two variances at once."
            ),
        ),
        MathBlock(
            label="Two-sided confidence interval",
            math=r"""
\hat{\delta} \;\pm\; t_{\alpha/2,\,\mathrm{df}} \cdot \mathrm{SE}
""",
            note=(
                "A CI on the **difference**, which is what makes it "
                "interpretable to stakeholders: '*the treatment lifts revenue "
                "by 2.30 to 1.10 units at 95%*' is much more actionable than "
                "'p = 0.03'."
            ),
        ),
        MathBlock(
            label="Hypothesis test — two-sided and one-sided",
            math=r"""
\begin{aligned}
H_1: \mu_1 \neq \mu_2 &\Longrightarrow p = 2 \cdot P\left(T_{\mathrm{df}} > |t|\right) \\
H_1: \mu_1 > \mu_2 &\Longrightarrow p = P\left(T_{\mathrm{df}} > t\right) \\
H_1: \mu_1 < \mu_2 &\Longrightarrow p = P\left(T_{\mathrm{df}} < t\right)
\end{aligned}
""",
            note=(
                "Same rule as the one-sample case. For one-sided variants the "
                "CI becomes a half-line, as before."
            ),
        ),
    ),
    assumptions=(
        "Observations independent within and between groups.",
        "Each group approximately normal — or n per arm large enough for the "
        "CLT.",
        "**Welch:** no equal-variance assumption (the point).",
        "**Student:** equal population variances (rarely checkable, often "
        "wrong).",
    ),
    advantages=(
        "Closed-form, powerful, and standard in every statistics package.",
        "Produces a CI on the effect size directly — ideal for business "
        "readouts.",
        "Welch is nearly as efficient as Student when variances are equal.",
    ),
    disadvantages=(
        "Sensitive to outliers on either arm.",
        "Assumes independence — silently wrong under network effects, shared "
        "sessions, or clustered users.",
        "The normal approximation breaks for very rare binary outcomes or "
        "tiny arms.",
    ),
    code="""from scipy import stats

# Welch (default — recommended)
stats.ttest_ind(a, b, equal_var=False)

# Student (only if you're confident variances are equal)
stats.ttest_ind(a, b, equal_var=True)

# One-sided upper
stats.ttest_ind(a, b, equal_var=False, alternative='greater')""",
)


# --------------------------------------------------------------------------- #
#  Card 3 — One-sided vs two-sided
# --------------------------------------------------------------------------- #
_ONE_VS_TWO = StatCard(
    id="one_vs_two",
    name="One-sided vs two-sided — the choice",
    tagline="When it's defensible to halve the p-value, and when it's p-hacking in disguise.",
    intro=(
        "The choice between one-sided and two-sided is a **design** decision, "
        "made before the data arrives. Two-sided is the safe default — it "
        "detects an effect in either direction, matches what journals and "
        "regulators expect, and needs no justification. One-sided is "
        "defensible when the opposite direction is either impossible or "
        "operationally irrelevant — and when you're willing to pre-commit in "
        "writing to the direction you're testing."
    ),
    math_blocks=(
        MathBlock(
            label="Rejection regions differ",
            math=r"""
\text{Two-sided:}\;\; |t| > t_{\alpha/2,\,\mathrm{df}}
\qquad\qquad
\text{One-sided:}\;\; t > t_{\alpha,\,\mathrm{df}}
""",
            note=(
                "Two-sided splits α across both tails, so each tail gets α/2. "
                "One-sided puts all of α in one tail. The observed |t| needs "
                "to be *larger* to reject two-sided, *smaller* to reject "
                "one-sided — that's the whole power gain."
            ),
        ),
        MathBlock(
            label="Critical-value comparison at α = 0.05",
            math=r"""
\alpha = 0.05,\;\; \mathrm{df} = \infty:\qquad
t_{0.025} = 1.96,\qquad t_{0.05} = 1.645
""",
            note=(
                "The one-sided critical value is about 16% smaller. For a fixed "
                "power target, one-sided designs need roughly **20% smaller "
                "samples**. For a fixed sample, they detect effects about 20% "
                "smaller."
            ),
        ),
        MathBlock(
            label="Confidence intervals — the asymmetry",
            math=r"""
\begin{aligned}
\text{Two-sided } 95\%\text{ CI:}\quad & \left[\hat{\delta} - 1.96\,\mathrm{SE},\;\hat{\delta} + 1.96\,\mathrm{SE}\right] \\[4pt]
\text{One-sided } 95\%\text{ CI:}\quad & \left[\hat{\delta} - 1.645\,\mathrm{SE},\;+\infty\right)
\end{aligned}
""",
            note=(
                "The one-sided interval is a **half-line** — bounded below, "
                "unbounded above. It can exclude 0 when the estimate is "
                "positive, but it tells you nothing about how large the "
                "effect might plausibly be. If upper-bound communication "
                "matters, use two-sided."
            ),
        ),
    ),
    assumptions=(
        "The direction is committed to in writing before the data arrives.",
        "The opposite direction is either physically impossible or "
        "operationally irrelevant (any effect → you ship; no effect → you "
        "don't).",
        "Reviewers or regulators will accept a one-sided test — many will "
        "not.",
    ),
    advantages=(
        "More power for the same n, or smaller n for the same power.",
        "Correct when the direction is genuinely one-sided — e.g. "
        "non-inferiority, one-way guardrails.",
        "Signals to stakeholders that the design reflects the actual "
        "business decision.",
    ),
    disadvantages=(
        "Easily abused — if the direction is chosen after seeing data, "
        "the p-value is meaningless.",
        "Ignores a real effect in the opposite direction, which can be "
        "costly in guardrail monitoring.",
        "Poorly received by journals, regulators, and many executives.",
    ),
    code="""from scipy import stats

# scipy defaults to two-sided
stats.ttest_ind(a, b, alternative='two-sided')   # default
stats.ttest_ind(a, b, alternative='greater')     # one-sided upper
stats.ttest_ind(a, b, alternative='less')        # one-sided lower""",
)


# --------------------------------------------------------------------------- #
#  Card 4 — A/B test end-to-end
# --------------------------------------------------------------------------- #
_AB_TEST = StatCard(
    id="ab_test",
    name="A/B test — end to end",
    tagline="Same three objects as a two-sample t-test, but wrapped in pre-registration, power analysis, and guardrails.",
    intro=(
        "An A/B test is a two-sample t-test on a randomised experiment. "
        "What makes it different is everything around the math: you "
        "pre-register the hypothesis and the MDE, size the test for a target "
        "effect, run for a fixed duration, and report the CI. For binary "
        "outcomes the same skeleton becomes a **two-proportion z-test** — "
        "identical logic, large-sample normal instead of t."
    ),
    math_blocks=(
        MathBlock(
            label="Pre-registration — decide everything before you run",
            math=r"""
\begin{aligned}
& \text{Hypothesis:} & & H_0:\,\delta = 0 \;\;\text{vs}\;\; H_1:\,\delta \neq 0 \\
& \text{Significance:} & & \alpha = 0.05 \\
& \text{Power:} & & 1 - \beta = 0.80 \\
& \text{Primary metric:} & & Y \\
& \text{Minimum detectable effect:} & & \delta^{*}
\end{aligned}
""",
            note=(
                "The MDE is the smallest effect you care to detect — not the "
                "smallest possible. Set it too small and n blows up; set it "
                "too large and you miss real effects. Pick it from the "
                "business case, not from the data."
            ),
        ),
        MathBlock(
            label="Estimator — continuous or binary outcome",
            math=r"""
\hat{\delta}_{\text{mean}} = \bar{y}_T - \bar{y}_C
\qquad
\hat{\delta}_{\text{prop}} = \hat{p}_T - \hat{p}_C
""",
            note=(
                "For continuous metrics the SE uses per-arm SDs; for binary "
                "metrics it uses per-arm proportions. CUPED, trimmed means, "
                "or regression adjustment reduce the variance without "
                "changing the point estimate — often the single biggest lever "
                "on experiment cost."
            ),
        ),
        MathBlock(
            label="Sample size (equal arms, continuous outcome)",
            math=r"""
n = \frac{2 \cdot (z_{1-\alpha/2} + z_{1-\beta})^2 \cdot \sigma^2}{(\delta^{*})^2}
""",
            note=(
                "σ² is the **per-user** variance of the outcome. For a binary "
                "metric, σ² = p(1−p) at the baseline rate. Shrinking σ² via "
                "CUPED or a tighter metric shrinks n quadratically."
            ),
        ),
        MathBlock(
            label="Minimum detectable effect (inverse view)",
            math=r"""
\mathrm{MDE} = (z_{1-\alpha/2} + z_{1-\beta}) \cdot \sigma \cdot \sqrt{\frac{2}{n}}
""",
            note=(
                "MDE shrinks as 1/√n — halving the required effect size "
                "quadruples the sample. That's the cost curve every A/B test "
                "lives on. Report the MDE in the readout; a wide CI around "
                "zero is **not** evidence of no effect, only evidence that "
                "you couldn't have detected one."
            ),
        ),
        MathBlock(
            label="Test and confidence interval at readout",
            math=r"""
\hat{\delta} \;\pm\; z_{1-\alpha/2} \cdot \mathrm{SE},
\qquad
z = \frac{\hat{\delta}}{\mathrm{SE}}
\qquad
p = 2 \cdot \Phi(-|z|)
""",
            note=(
                "For large n, the t and z versions converge — the readout uses "
                "z for simplicity. Report the CI **and** the effect size, "
                "not just 'significant at p < 0.05'."
            ),
        ),
        MathBlock(
            label="Readout — statistical vs practical significance",
            math=r"""
\begin{aligned}
& \text{Statistical:} & & |z| > z_{1-\alpha/2} \\
& \text{Practical:} & & |\hat{\delta}| > \delta_{\text{business}}
\end{aligned}
""",
            note=(
                "A statistically significant effect can be too small to be "
                "worth shipping. Require **both** columns to be true, and "
                "always check guardrails (latency, revenue per user, churn) "
                "for regressions — a positive primary metric with a broken "
                "guardrail is a net negative."
            ),
        ),
    ),
    assumptions=(
        "Randomisation is unbiased — the sample ratio mismatch (SRM) check "
        "must pass, or the test is invalid.",
        "Users are independent — no network effects, no shared sessions, no "
        "clustered assignment.",
        "Outcome is approximately normal per arm, or n is large enough for "
        "the CLT.",
        "Duration covers a full business cycle — weekly seasonality, novelty "
        "effects, and primacy effects all need time to wash out.",
    ),
    advantages=(
        "Causal identification — randomisation removes confounding.",
        "Closed-form math — no ML required for the basic readout.",
        "The CI converts directly into a decision: is the lower bound above "
        "the business threshold?",
    ),
    disadvantages=(
        "Requires pre-registration — retrospective A/B tests are a different "
        "discipline.",
        "**Peeking** inflates type I error; needs sequential-testing "
        "corrections (alpha spending, group sequential design).",
        "Multiple metrics need multiple-comparison correction (Bonferroni or "
        "Benjamini–Hochberg).",
        "Underpowered tests read as 'no effect' — a wide CI around zero is "
        "not evidence of equivalence.",
    ),
    code="""from statsmodels.stats.power import TTestIndPower
from statsmodels.stats.proportion import proportions_ztest

# Design: sample size for a target standardized effect
TTestIndPower().solve_power(
    effect_size=delta / sigma,   # Cohen's d
    alpha=0.05, power=0.80,
    ratio=1, alternative='two-sided',
)

# Readout: two-proportion z-test
z, p = proportions_ztest([x_treat, x_ctrl], [n_treat, n_ctrl])

# For continuous metrics:
# from scipy import stats
# stats.ttest_ind(a, b, equal_var=False)""",
)


CARDS: tuple[StatCard, ...] = (
    _ONE_SAMPLE,
    _TWO_SAMPLE,
    _ONE_VS_TWO,
    _AB_TEST,
)
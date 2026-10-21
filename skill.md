---
name: ml-ds-ai-quiz-dataset
description: Generate, extend, or audit CSV multiple-choice question datasets for ML / Data Science / AI consulting interview preparation. Targets Artefact, Emerton, Jakala and BCG X. Use whenever creating a new batch of questions, adding rows to questions.csv, or reviewing existing questions for quality.
---

# ML / DS / AI Consulting — Quiz Dataset Generator

## 1. Purpose & scope

Produce interview-grade multiple-choice questions for candidates targeting
**Artefact, Emerton, Jakala, and BCG X**. The output is a CSV consumed by a
Streamlit quiz app that renders LaTeX.

This skill covers **question authoring only**. It does not cover app code,
deployment, or non-MCQ formats (cases, guesstimates, coding screens).

## 2. Audience calibration

Write for a candidate with **2–5 years of analytics/DS experience applying to a
consulting-track role**. Assume:

- Fluent in Python/SQL and standard ML library vocabulary.
- Has shipped or at least read about models in production.
- Is **not** a deep-learning researcher — no backprop derivations, no
  transformer architecture internals.
- Will be judged in interviews on: judgment, framing, tradeoffs, and the
  ability to explain to a non-technical client.

Firm flavour to lean into:

| Firm | Lean toward |
|---|---|
| Artefact | Data/ML engineering realism, recommender & marketing analytics, LLM productisation |
| Emerton | Business framing, estimation, market sizing, healthcare/industrial verticals |
| Jakala | Customer & marketing analytics, segmentation, CLV, personalisation |
| BCG X | AI strategy, governance, end-to-end delivery tradeoffs, GenAI productisation |

## 3. Hard contract — CSV schema

Header row, exactly this order, exactly these names (lowercase, snake_case):

```
question,answer1,answer2,answer3,answer4,correctanswer,explanation,theme,difficulty,secondary_themes,vertical
```

### Field rules

| Field | Required | Rules |
|---|---|---|
| `question` | yes | Single sentence preferred; max ~40 words. LaTeX allowed. |
| `answer1`–`answer4` | yes | All four must be present and non-empty. LaTeX allowed. |
| `correctanswer` | yes | Use the **option number** `1`–`4` — always. Text matching is fragile. |
| `explanation` | yes | 2–4 sentences. Must explain *why correct* **and** *why the most tempting distractor is wrong*. LaTeX allowed. |
| `theme` | yes | Exactly one value from the **primary taxonomy** in §4. |
| `difficulty` | yes | `easy` / `medium` / `hard`. See rubric §6. |
| `secondary_themes` | optional | `;`-separated list from the same taxonomy. Leave empty if none. Max 2. |
| `vertical` | yes | `;`-separated list from §5. Use `general` when industry-agnostic. |

### CSV mechanics

- UTF-8, no BOM, one header row, one row per question.
- **Quote every field that contains a comma, quote, or newline.** Safest:
  quote every field.
- No trailing blank rows, no repeated headers mid-file.
- Do not embed the delimiter inside a field without quoting.
- Never use a literal newline inside a field — keep the question on one line.

## 4. Primary theme taxonomy

`theme` must be **exactly one** of these strings (case-sensitive):

### Core technical

| Theme | Scope | Do **not** file here |
|---|---|---|
| `Statistics & Probability` | Distributions, hypothesis tests, confidence intervals, Bayes, sampling, variance | Model metrics |
| `Classical ML` | Bias–variance, regularisation, trees/boosting, feature engineering & importance, train/test discipline | Deep learning, LLMs |
| `Model Evaluation` | Metric choice (AUC vs PR, F1, MAE), calibration, cross-validation strategy, leakage | The statistics of the metric itself |
| `Experimentation & A/B Testing` | Power/MDE, peeking, guardrail & OEC metrics, network effects, sequential tests | Causal inference outside experiments |
| `SQL & Data Manipulation` | Joins, window functions, dedup, grain, NULL semantics, aggregation traps | Warehouse tooling trivia |

### 2026 differentiators

| Theme | Scope | Do **not** file here |
|---|---|---|
| `LLMs & Generative AI` | RAG vs fine-tuning, prompt/context design, evaluation of generative output, hallucination mitigation, agent design, token/cost tradeoffs | GPU/infra ops |
| `MLOps & Production` | Drift detection, monitoring, retraining triggers, CI/CD for models, reproducibility, serving | Model *choice* |
| `Causal Inference` | DiD, IV, propensity scores, confounding, uplift, when A/B is impossible | Experimental design (that's A/B) |

### Firm-flavoured

| Theme | Scope | Do **not** file here |
|---|---|---|
| `Business Framing & Estimation` | Unit economics, funnel math, sizing approach selection, translating business ask into a metric | Pure arithmetic |
| `Marketing & Customer Analytics` | CLV, segmentation, churn, attribution, personalisation metrics | General ML |
| `AI Governance & Responsible AI` | Regulation (EU AI Act, GDPR), fairness metrics, model risk, PII, auditability | Model performance |

**Filing rule:** tag by **the skill being tested**, not the topic merely
mentioned. A question about choosing a metric for a fraud model is
`Model Evaluation`, not `Business Framing & Estimation` — even if it's phrased
as a client ask.

**Secondary themes:** add only if a competent interviewer would probe the
question from two distinct angles. Two is the ceiling. Never duplicate the
primary.

## 5. Vertical taxonomy

`general`, `finance`, `healthcare`, `retail`, `telecom`, `energy`, `marketing`

- `general` = the question's answer would be identical in any industry.
- Use `general` **plus** a specific vertical only if the setting matters but the
  answer also generalises (e.g. `healthcare;general`). Prefer a single specific
  vertical when the answer genuinely depends on it.
- **Target mix per 20 questions:** ~8 `general`, ~2 each of `finance`,
  `retail`, `marketing`, ~1 each of `healthcare`, `telecom`, `energy`. Emerton
  skews healthcare/industrial; Jakala skews marketing/retail.
- Never invent a vertical outside the list. Propose a new one explicitly.

## 6. Difficulty rubric

| Level | Test | Signal |
|---|---|---|
| `easy` | Recall or one-step application of a single concept | A strong final-year student answers correctly without hesitation |
| `medium` | Apply a concept to a scenario, or discriminate between two plausible methods | Requires one inference beyond the definition |
| `hard` | Multi-step reasoning, edge cases, or rejecting a distractor that is correct on a technicality | A working consultant may still pause; explanation has real content |

**Target mix per 20 questions:** 5 easy, 10 medium, 5 hard. Never more than
~10% easy in an expansion batch — easy questions pad the set without testing
interview readiness.

## 7. LaTeX conventions

The app renders with KaTeX via `st.markdown`.

- Inline math: `$...$` — e.g. `$P(A \mid B)$`
- Display math: `$$...$$` — use only when the expression is genuinely central
- Use `\mid` for conditioning bars, **not** `|`
- Wrap words inside math in `\text{}` — e.g. `$\text{MSE} = \frac{1}{n}\sum_i (y_i - \hat{y}_i)^2$`
- **Currency: always escape the dollar sign as `\$`.** A bare `$` opens math
  mode and silently mangles everything after it. This is the single most
  common breakage — check every monetary question.
- Don't mix unicode symbols (Σ, ≥, →) inside LaTeX blocks; use `\sum`,
  `\geq`, `\to`. Unicode is fine outside math.
- Keep expressions short enough to fit one line in a radio button label.
- Backslashes are safe in CSV; commas inside math are fine **if the field is
  quoted**.

## 8. Question writing rules

**Stem**
- One scenario or one question. No multi-part asks.
- Give every number needed to answer; don't require a calculator.
- Name the decision being made, not just the topic.

**Options**
- Exactly one unambiguously correct option.
- All four options should be **the same grammatical form and similar length**
  — length is a tell.
- Distractors must encode a **real misconception**, not random noise.
- No `all of the above`, `none of the above`, `both A and B`.
- Avoid absolutes (`always`, `never`) in the correct answer.
- Don't make the correct answer the longest or most hedged option.

**Explanation**
- Sentence 1–2: why the correct option is right (show the calculation if any).
- Sentence 3: name the tempting distractor and why it fails. This is the
  highest-value part for interview prep.
- No filler ("This is a common concept…"). No restating the question.

## 9. Anti-patterns — reject these

- ❌ Trivia that tests vocabulary rather than judgment ("What does AUC stand for?")
- ❌ Questions answerable by eliminating implausible options without knowing the concept
- ❌ Topic name in the stem giving away the framework ("In a bias–variance context, …")
- ❌ Two options that are both defensible — ambiguity kills the dataset
- ❌ Explanation that only justifies the correct answer and ignores distractors
- ❌ Unescaped `$` before a number
- ❌ Duplicate/near-duplicate questions across batches (always diff against existing rows)
- ❌ Deep-learning theory, OR/optimisation, cloud-vendor certification trivia —
  out of scope for these firms
- ❌ Difficulty inflation: tagging everything `hard` to look rigorous

## 10. Batch generation workflow

1. **Confirm the brief** before writing anything: total count, theme
   distribution, difficulty mix, vertical mix, and whether this is a new file
   or an append.
2. **Draft** rows one at a time. Vary the stem shape — don't produce 20
   questions that all start with "A client wants to…".
3. **Self-check** against §11.
4. **Emit** a single fenced ```csv block containing the header row and all
   rows. No commentary inside the block.
5. **Report** a one-line summary after the block: row count and the
   theme × difficulty distribution actually produced.
6. If appending, state explicitly that rows should be **appended**, not
   replace the file, and remind the user to re-run the app.

Default batch size: **20 questions**. Larger batches degrade distractor
quality — split into rounds.

## 11. Self-check before emitting

- [ ] Header matches §3 exactly
- [ ] Every row has all 11 fields
- [ ] Every `correctanswer` is `1`–`4` (digit, quoted)
- [ ] Every `theme` is verbatim from §4
- [ ] Every `vertical` value is from §5
- [ ] Every `difficulty` is `easy` / `medium` / `hard`
- [ ] No unescaped `$` before a digit anywhere
- [ ] Every LaTeX block opens and closes
- [ ] All fields with commas are quoted
- [ ] Difficulty and theme distributions match the brief
- [ ] No two rows test the same concept
- [ ] Each explanation names the tempting distractor
- [ ] No anti-pattern from §9 present
- [ ] Row count matches the brief

## 12. Calibration examples

These are style anchors, not part of the dataset.

```csv
"question","answer1","answer2","answer3","answer4","correctanswer","explanation","theme","difficulty","secondary_themes","vertical"
"A model has precision $0.60$ and recall $0.40$. What is its F1 score, to two decimal places?","$0.48$","$0.50$","$0.24$","$1.00$","1","F1 is the harmonic mean of precision and recall: $F_1 = 2 \cdot \frac{P \cdot R}{P + R} = 2 \cdot \frac{0.24}{1.00} = 0.48$. The tempting answer $0.50$ is the arithmetic mean, which overstates performance whenever precision and recall are imbalanced.","Model Evaluation","medium","Statistics & Probability","general"
"A legal-tech client needs an assistant that answers questions on legislation updated weekly, and every answer must cite the source clause. Which approach is most appropriate?","Fine-tune the base model on the legislation every week.","Retrieve relevant clauses at query time and pass them in the prompt.","Rely on strong prompt engineering on the base model.","Distill a smaller model on the legal corpus.","2","Retrieval keeps the corpus external, so a weekly update is a re-indexing job rather than a retraining cycle, and the retrieved chunks provide the citation. Fine-tuning teaches style and format but does not reliably inject fresh facts and offers no native provenance.","LLMs & Generative AI","hard","MLOps & Production","general"
"A subscription business charges \$30 per month, has 5% monthly churn and an 80% gross margin. What is the approximate customer lifetime value?","\$24","\$480","\$600","\$1,500","2","LTV is gross-margin revenue per period divided by churn: $30 \times 0.8 / 0.05 = \$480$. The tempting answer \$600 uses revenue instead of gross margin, which overstates value by exactly the margin factor.","Business Framing & Estimation","medium","Marketing & Customer Analytics","general"
```

---

**Maintenance:** when a new primary theme or vertical is added, update §4/§5
**and** the Streamlit app's landing-page schema description in the same change,
so the docs never drift from the code.
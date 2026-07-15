# **LLM‑Based CV Gender Bias Analysis**

This repository contains the pipeline used to investigate whether **prompting technique modulates gender-based scoring disparity** when Large Language Models (Claude Opus 4.5 and GPT-5.2) are used for automated CV screening. LLMs are increasingly adopted for CV evaluation for their consistency and scalability, but they can carry systematic demographic biases from their training and alignment, and gender signals cannot be fully neutralized even when explicit identifiers are removed.

This pipeline evaluates 457 CV triplets (male, female, and neutral versions) across eight professional domains, under seven prompting techniques (Zero-Shot, Few-Shot, Chain-of-Thought, Thread-of-Thought, Self-Consistency, Least-to-Most, and Take-a-Step-Back) and five robustness checks (explicit pronouns, an explicit gender field, implicit hobbies cues, a coarser scoring scale, and an explicit fairness instruction). Bias is assessed through a multi-metric framework, mean score differentials, rank-based analysis, severity classification, score range sensitivity, and domain-level effects, alongside a human validation check and a formal cross-technique statistical comparison, to test whether the choice of prompting technique itself shapes the degree of gender bias produced.

The structure is modular, but all experiments derive from the **main pipeline**, altering only inputs or prompts.

\---

## **1. General Structure**

```text
data/                 			→ original Cvs and JDs
src/Preprocessing and CV Selection/     → scan gender signals + cleaning + injection
src/JD selection/			→ leaning of JDs and top 10 selection by overlap mean rank
src/Pipeline/         	→ main pipeline (Claude/GPT) and prompts (scoring scale, fairness instruction, etc.)
src/Robustness Checks/       		→ reliability run + JD sensitivity
src/Human Validation/          	→ CV sampling for manual scoring + human vs. LLM comparison (MAE, Spearman)
src/Bias Analysis/        	 	→ analysis scripts, including the cross-technique Friedman/Wilcoxon test
```

\---

## **2. Pipeline Flow**

### **A. Preprocessing and CV Selection (mandatory before any experiment)**

1. **Scan Gender Signals**: Extracts gender signals from the original CVs.
2. **CV Cleaning \& Names Injection**: Cleans CVs and injects names, pronouns, gender fields, and hobbies when necessary.
3. **Job Description Selection**: Uses the JD script to select:

   * the **main JD** - the **5 JDs** for JD sensitivity  
(the script returns 10; the final selection is manual).

All scripts require manual updating of **input/output paths**.

\---

### **B. Main Pipeline (core of all experiments)**

The main pipeline is the central script that:

* receives CVs (original or manipulated)
* receives the selected JD
* loads the base prompt
* sends to Claude or GPT
* outputs 0–10 scores

There are two versions:

* `scoring\_pipeline\_claude.py`
* `scoring\_pipeline\_gpt.py`



All scripts require manual updating of **input/output paths**.

\---

### **C. Manipulated Experiments (pronouns, gender, hobbies)**

These **do not have their own scripts**.  
They use **exactly the main pipeline**, only with:

* **different inputs** (manipulated CVs)
* **different paths** (input/output)

> Experiment = main pipeline + manipulated CVs



All scripts require manual updating of **input/output paths**.

\---

### **D. Prompt Experiments (scoring scale, fairness instruction)**

These also use **the main pipeline**, but with:

* **different prompts**, loaded from the `.txt` files in
* **different paths** to save the results

> Experiment = main pipeline + alternative prompt

The fairness instruction changes **only the system prompt**.  
The scoring scale changes **only the scoring section**.



All scripts require manual updating of **input/output paths**.

\---

### **E. Robustness Checks**

1. **Reliability Run** Repeats the main pipeline multiple times with the same setup. Use `reliability\_run\_trigger.py` to run the reliability run scripts (change the name of the python file `reliability\_run\_gpt/claude.py` to run the correct script)
2. **JD Sensitivity** Runs the main pipeline with different JDs.



All scripts require manual updating of **input/output paths**.

\---

### **F. Human Validation**

1. **CV Sampling for Manual Scoring** Selects a subset of neutral-version CVs (stratified by domain and length) for the researcher to score manually, independently of any model output.
2. **Human vs. LLM Comparison** Merges the human scores with the corresponding LLM scores for each of the seven techniques, for both models, and computes the Mean Absolute Error (MAE) and Spearman's rank correlation between human and LLM scores per technique, per model, as a concurrent validity check on the scoring instrument.



All scripts require manual updating of **input/output paths**.

\---

### **G. Analysis**

Dedicated scripts for:

* Main experiments
* Reliability
* JD sensitivity
* **Cross-technique comparison**: a Friedman test was applied to each condition, treating the rank gap per CV pair as a repeated measure across the seven techniques, followed where significant by Bonferroni-corrected pairwise Wilcoxon tests across all 21 technique pairs.

They generate metrics, tables, and figures.



All scripts require manual updating of **input/output paths**.

\---

## **3. Important Notes**

* The pipeline **is not executed automatically**; each step is manual.
* The **input/output paths** must be adjusted for each experimente as referred throught this guide.
* Claude and GPT have separate pipelines.
* Alternative prompts are located in `Pipeline` and are loaded by the main pipeline.

\---


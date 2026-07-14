# **LLM‑Based CV Gender Bias Analysis**

This repository contains the pipeline used to analyze **gender bias in CV evaluation by LLMs** (Claude and GPT). The structure is modular, but all experiments derive from the **main pipeline**, altering only inputs or prompts.

\---

## **1. General Structure**

```text
data/                 			→ original Cvs and JDs
src/Preprocessing and CV Selection/     → scan gender signals + cleaning + injection
src/JD selection/			→ leaning of JDs and top 10 selection by overlap mean rank
src/Pipeline/         			→ main pipeline (Claude/GPT) and prompts (scoring scale, fairness instruction, etc.)
src/Robustness Checks/       		→ reliability run + JD sensitivity
src/Bias Analysis/        	 	→ analysis scripts
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

### **F. Analysis**

Dedicated scripts for:

* Main experiments
* Reliability
* JD sensitivity

They generate metrics, tables, and figures.



All scripts require manual updating of **input/output paths**.

\---

## **3. Important Notes**

* The pipeline **is not executed automatically**; each step is manual.
* The **input/output paths** must be adjusted for each experimente as referred throught this guide.
* Claude and GPT have separate pipelines.
* Alternative prompts are located in `Pipeline/` and are loaded by the main pipeline.

\---


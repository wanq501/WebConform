# WebConform

**Decision-level conformance testing of multimodal web agents against operation semantics.**

A web agent that clicks *Add to Bag* before the gift message is typed, and one that clicks it once the message is typed, make the
same click. Only the first breaks the task. Element accuracy cannot tell a premature commit from a harmless wrong click, and an
action-risk label cannot tell it from the commit the task requires. WebConform judges every decision of an agent against the
operation semantics of the web (HTTP safe and idempotent methods, preconditions of state changes) and fixes the verdict before
the agent is queried, so it needs no deployed website and executes no action.

![Three decisions on one page under three oracles](docs/challenge.png)

WebConform has four mechanisms:

* **Operation-semantic relations (OSR)** state when a state-changing control is forbidden: on a read-only task (R1), before the
  commit step of a state-changing task (R2) and after it (R3).
* **Semantic control classification (SCC)** decides whether a control changes state by the request it issues, not by its label.
* **Demonstration-derived probing (DDP)** turns each recorded step of a benchmark of demonstrations into a test case with a known verdict.
* **Counterfactual precondition pairing (CPP)** copies a commit state and erases one typed input, so that two pages differ in one precondition.

![Overview of WebConform](docs/overview.png)

## Results of the paper

Eight multimodal large language models (MLLMs), 4,533 test cases from the three test splits of Multimodal-Mind2Web, vanilla setting,
pooled over the eight MLLMs. A ratio above 1 means the agents choose the forbidden control more often than a random choice would.

| Relation | Violation rate | Chance level | Ratio |
|---|---:|---:|---:|
| R1 safety (read-only tasks) | 0.4% | 2.2% | 0.19 |
| R2 precondition (before the commit) | 17.4% | 9.5% | 1.83 |
| R3 idempotency (after the commit) | 12.0% | 7.4% | 1.62 |
| Counterfactual pairs, input erased | 30.0% | 4.0% | 7.50 |

Oracles against the majority verdict of an independent panel of three MLLM judges on 286 validation decisions (%):

| Oracle | Precision | Recall | F1 | Accuracy |
|---|---:|---:|---:|---:|
| **WebConform** | 46.2 | 72.7 | 56.5 | 87.1 |
| Action-risk label | 27.3 | 100.0 | 42.9 | 69.2 |
| Element accuracy | 16.3 | 90.9 | 27.6 | 45.1 |

## Repository

```
webconform/            the test as a Python package: prompts, answer parser, oracle, bundle reader, API client
  run.py               python -m webconform.run    one setting on a test suite bundle with one model
  score.py             python -m webconform.score  violation rate, chance level, ratio and exact test per relation
harness/atelier/       the module of the experiment console that ran the study (reference implementation)
analysis/              every number, table and figure of the paper, computed from data/
  figures/             the 24 figures (figure scripts, method figures in figures/design)
  supplement/          Supplementary File 1 (PDF) and the data files of Supplementary File 2
data/export/           the experiment export: test cases (screens.csv), all 41,736 decisions (results.json), panel votes
data/curated/          126 test cases with their screenshots, used by the case figures and the supplement
data/main_set.txt      the 1,617 test cases of the main set
tests/run_tests.py     tests of the package against the experiment
reproduce.py           reproduces the paper from data/
```

## Installation

Python 3.10 or later.

```
git clone https://github.com/wanq501/WebConform.git
cd WebConform
pip install -r requirements.txt
```

The figures and the supplement also need a LaTeX installation with `pdflatex`. The package itself needs only the standard library.

## Reproducing the paper

```
python reproduce.py            # numbers and tables, checked byte for byte against the reference outputs (under a minute)
python reproduce.py --all      # also the 24 figures and the supplementary material (about two minutes)
python tests/run_tests.py      # the package against the experiment
```

`tests/run_tests.py` checks that the answer parser reads all 41,736 stored answers exactly as the experiment did, that the oracle
gives the forbidden set and the chance level of the paper on all 4,780 test cases, that the prompts are identical to those of the
experiment console (rendered with Node.js when it is installed), and runs the package end to end against a mock API server.

## Testing an agent

The test runs on a test suite bundle, a ZIP archive in the format `webconform-bundle/1` with `manifest.json`, `probes.jsonl` (one test
case per line, with the task, the candidate controls and their flags, and the name of the screenshot) and the screenshots. The bundle of
the paper, `WebConform-Probes.zip`, is attached to the release of this repository.

Any model behind an OpenAI-compatible chat API can be tested, for example a local model served with vLLM:

```
vllm serve Qwen/Qwen3-VL-8B-Instruct --served-model-name qwen3-vl-8b --port 8000 --seed 0
python -m webconform.run   --bundle WebConform-Probes.zip --ids data/main_set.txt --base-url http://127.0.0.1:8000/v1 \
                           --model qwen3-vl-8b --setting s0 --out qwen3vl8b_s0.jsonl
python -m webconform.score --bundle WebConform-Probes.zip --ids data/main_set.txt --decisions qwen3vl8b_s0.jsonl
```

or a model behind a provider API, with the key in an environment variable and provider options passed through:

```
export OPENAI_API_KEY=...
python -m webconform.run --bundle WebConform-Probes.zip --ids data/main_set.txt --base-url https://api.example.com/v1 \
       --model <model> --setting s0 --out s0.jsonl --extra-body '{"reasoning": {"effort": "low"}}'
```

Settings: `s0` vanilla, `s1` action history, `s2` rule instruction, and the second-stage guardrails `sc` self-check, `rg` risk gate,
`cv` commit verification and `cvx` commit verification with explanation, which need the `s0` decisions of the same model
(`--proposals s0.jsonl`). All calls use temperature 0 and at most 4,096 output tokens. A run can be interrupted and resumed.

## Data

`data/export` is the export of the experiment console. `screens.csv` lists the 4,780 test cases with their relation, split, website,
task, option tags and the letters of the demonstrated, commit and state-changing controls. `results.json` holds every decision of the
eight MLLMs in every setting, with the raw answer, the parsed letter, token usage and latency, and `tables/` the votes of the
validation panel. The screenshots of `data/curated` are crops of the screenshots of the public Multimodal-Mind2Web test splits
(osunlp/Multimodal-Mind2Web) and are subject to the license of that dataset.

## Citation

```
@article{wan2026webconform,
  title   = {WebConform: Decision-Level Conformance Testing of Multimodal Web Agents Against Operation Semantics},
  author  = {Wan, Qian and Huang, Ping and Wan, Zhijun and Zhao, Junming},
  year    = {2026},
  note    = {Manuscript under review}
}
```

## License

The code is released under the MIT License. The data derived from Multimodal-Mind2Web follow the license of that dataset.

# Reference harness

`webconform.js` is the WebConform module of Atelier, the experiment console with which the study was run. It holds the prompts
(`E.SYSTEM`, `E.GUARD`, `E.CV_CHECKS`, `E.CVX_CHECKS`, `E.RG_CHECK`, `E.SC_CHECK`, `E.userText`), the option lists (`E.makeQuestion`),
the validity filters (`E.validate`, `E.cfPairOk`), the main set (`E.assignSubsets`), the answer parser (`E.parse`, `E.metrics`), the
oracle (`E.violLetters`, `E.chance`) and the validation panel (`E.JUDGE_SYSTEM`, `E.judgePrompt`, `E.judgeSample`).

The module runs inside the console and is published as the reference for the Python package in `webconform/`, which reproduces its
prompts, parser and oracle. `tests/run_tests.py` renders the prompts of both and checks that they are identical.

# Experiment export

Export of the WebConform experiment from the console, format `mtgui-export/4`, exported on 9 November 2026.

| File | Content |
|---|---|
| `screens.csv` | the 4,780 test cases: relation, split, website, domain, task, step, number of options, letters of the demonstrated (`gold_letters`), commit (`repeat_letters`), state-changing (`write_letters`, `strict_letters`) controls, the option of no action (`none_letter`), the tag of every option (`option_tags`), subsets and validity |
| `results.json` | every decision of the eight MLLMs in every setting (`records`: model tag, test case, setting, raw answer, parsed letter, token usage, latency, attempts), the models and the run configuration |
| `models.csv`, `conditions.csv` | the models and the settings with their cost |
| `tables/08_panel_votes_r1.csv`, `tables/08_panel_votes_r2.csv` | the votes of the three judges in the calibration and the validation round |
| `tables/*.csv` | summary tables written by the console |

`analysis/analysis.py` reads this folder (or the folder in the environment variable `WC_EXPORT`).

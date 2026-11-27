# Character Consistency Bench (TUTAR)

[![tests](https://github.com/Biontra/character-consistency-bench/actions/workflows/tests.yml/badge.svg)](https://github.com/Biontra/character-consistency-bench/actions/workflows/tests.yml) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

TUTAR is a small benchmark that measures whether video models can keep a character intact while making that character do something.

5 video models, 1 start image, 20 commands, 98 clips, 103 yes/no questions. Scored by a judge model and checked by hand on 20 clips.

## Results

Full tables, counts and charts are in [`results/RESULTS.md`](results/RESULTS.md) (in Turkish). Read the two columns separately; they are not added up.

| Model | Generated | Did the command | Kept the character |
|---|---|---|---|
| Kling 3.0 | 20/20 | 100.0% (21/21) | 84.1% (254/302) |
| Wan 3.0 | 20/20 | 90.9% (20/22) | 92.1% (281/305) |
| Seedance 2.0 Mini | 20/20 | 95.5% (21/22) | 96.1% (292/304) |
| Grok Video 1.5 Lite | 20/20 | 90.0% (18/20) | 94.3% (248/263) |
| Gemini Omni Flash 1.2 | 18/20 | 86.4% (19/22) | 90.9% (250/275) |

![Dot plot: Kling did every command but kept the character least](results/chart_did_kept.svg)

### Findings

- **Doing the command and keeping the character are different skills.** Kling 3.0 did every command (100%) and kept the character least (84.1%).
- **Seedance 2.0 Mini kept the character best (96.1%) and was the cheapest**, at 0.34 credits per correct character answer. Gemini Omni Flash 1.2 was the most expensive at 0.81.
- **Questions written for one specific command were the hardest for every model.** All five models score lower on them than on the questions asked for every clip.
- **One model refused 2 of the 20 commands** (Gemini Omni Flash 1.2, safety filter). A refused command counts as not done.
- **The judge is not good enough to rank close models.** It agreed with my hand scores on 80.2% of answers; I had set 85% in advance.
- **No local open-source model could replace the judge.** The best got 5 of 10, which is a coin flip.

Human check: I scored 20 clips by hand. The judge agreed with me on 80.2% of answers; the threshold I wrote in advance was 85%, so **the check did not pass** and the table is one judge's reading, not a settled ranking.

## Example questions

A real command from the benchmark (all 20 are in [`data/commands.json`](data/commands.json)):

> She takes the plush toy and hugs it.

The model gets the start image and this sentence, and returns a 5 second video. The judge then answers a list of yes/no questions about that video.

### Public sample questions

I wrote 60 more questions of the same kind for the shared NEXA benchmark. They are public and are not part of the private set: [`sorular/Biontra.csv` in nexa-lab-ai/nexa-bench](https://github.com/nexa-lab-ai/nexa-bench/blob/main/sorular/Biontra.csv) (10 written by hand, 50 synthetic). Two of the hand-written ones, translated from Turkish:

| Scene and command | What the video must get right |
|---|---|
| A man with curly hair and a red sweater stands in a kitchen. Command: he opens the fridge, takes a tomato and bites it. | He takes one tomato · juice runs from where he bit · the inside of the tomato is not broken |
| Same man, same kitchen. Command: he cracks an egg into the pan. | The egg white sets in a believable shape · the shell breaks properly · the egg flows properly |

## Limits

One character, one start image, one try per command, one judge, 20 commands. Three of the five models are cheap tiers. 77 of the 103 questions were written by hand. Small gaps between models were not tested for significance.

## Links

| What | Where |
|---|---|
| Results page (mini leaderboard) | https://biontra.github.io/character-bench.html |
| Dataset (gated, manual approval) | https://huggingface.co/datasets/Biontra/character-consistency-bench |
| Method, question types, more charts | [`docs/DETAILS.md`](docs/DETAILS.md) |
| Full result tables (Turkish) | [`results/RESULTS.md`](results/RESULTS.md) |
| Rules written before the runs (Turkish) | [`PROTOCOL.md`](PROTOCOL.md) |
| The 20 commands | [`data/commands.json`](data/commands.json) |
| The judge prompt | [`judge/judge_prompt_v1.txt`](judge/judge_prompt_v1.txt) |
| Local model side test | [`results/local_models/README.md`](results/local_models/README.md) |
| Portfolio | https://biontra.github.io |

## How to run

Python 3 and ffmpeg (Homebrew path on macOS). Nothing else to install.

```bash
git clone https://github.com/Biontra/character-consistency-bench.git
cd character-consistency-bench
python3 -m unittest discover -s tests
```

Rebuilding the tables needs the private question file from the gated dataset; the command is in [`docs/DETAILS.md`](docs/DETAILS.md#how-to-run).

## Contact and license

Kaan Yunus Emre Akgöz · kaan102006@gmail.com · [github.com/Biontra](https://github.com/Biontra)

Code and public results: MIT, see [`LICENSE`](LICENSE). The gated dataset has its own terms (evaluation only).

# Local open-source vision models as a judge (10 questions)

A small side test, not part of the benchmark score. Six open-source vision models ran on a laptop through Ollama and answered 10 of the benchmark's check questions. The correct answer is the human score (the locked hand scoring of the 20 seeded clips).

Hardware: MacBook, Apple M4, 16 GB RAM. Ollama 0.32.15. Cost: 0 (no network, no fee). Date: 27 November 2026.

| Model | Correct (strict) | Correct (lenient) | Answers given | s/question | Size (GB) |
|---|---|---|---|---|---|
| llava:7b | 5/10 | 5/10 | no 10 | 9.3 | 4.7 |
| qwen2.5vl:3b | 5/10 | 5/10 | yes 6, no 3, not visible 1 | 10.9 | 3.2 |
| granite3.2-vision | 0/10 | 4/10 | yes 1, no 8, not visible 1 | 37.4 | 2.4 |
| gemma3:4b | 3/10 | 3/10 | yes 7, not visible 3 | 7.3 | 3.4 |
| moondream | 0/10 | 1/10 | yes 1, unreadable 9 | 2.6 | 1.7 |
| llava-phi3 | 0/10 | 0/10 | unreadable 10 | 4.3 | 2.9 |
| Claude Sonnet (the benchmark's judge, cloud) | 8/10 | 8/10 | yes 5, no 5 | not measured | - |

## How it was done

- `yerel_dene.py` picks the questions with a fixed seed (6): 5 where the human said yes and 5 where the human said no, only from questions that both the human and the judge answered with yes or no. They were not picked by hand.
- Each model gets one image per question: the first, middle and last frame of the clip side by side. The question is asked in Turkish, once, at temperature 0.
- **Strict** counts an answer only if the model wrote exactly `evet`, `hayir` or `gorunmuyor`. This rule was written before the run.
- **Lenient** also accepts English "yes" / "no". This column was added after seeing the outputs, because one model understood the question and answered in English. The strict column is the main number.

## What it shows, and what it does not

- No local model beat chance. Half of the questions have "yes" as the correct answer, so a model that always gives the same answer gets 5/10. llava:7b answered "no" ten times.
- The comparison is not equal: the Claude judge saw 50 frames per clip plus top and bottom crops; the local models saw 3 frames in one image.
- Ten questions is a very small sample. This is a trial, not a ranking of these models.
- s/question leaves out the first question (model loading) and answers served from cache (under 2 s). The llava:7b time is wall-clock from a separate run; the others come from Ollama's own duration field.
- The judge's time and per-question cost were not recorded when the benchmark ran.

Question text, per-question answers and raw model outputs are not in this folder; the raw outputs can echo parts of the private questions. The scripts read the private files from `secret/`, which is not in this repo.

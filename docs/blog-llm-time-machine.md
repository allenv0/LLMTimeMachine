# What if you could time-travel through a decade of LLMs?

Most people didn’t watch language models grow up. One day the chatbots were toys; the next day they write legal memos. If you weren’t there for GPT-2 in 2019, the progress is just a slide in someone else’s talk.

We wanted a different way in: not a benchmark chart, but a small machine that runs *your* prompt through a stack of old models and shows you the answers in order.

## The idea

Fire up an old checkpoint. Ask it the same weird question you’d ask today. Then the next year’s model. And the next.

Not “the best model of every year” — we can’t verify that, and pretending we can is how these demos lose people. What we built instead is an honest sample: a few open weights that fit on a laptop, pinned revisions, visible prompt wrappers, and every intermediate string you can open and check.

We called it the LLM Time Machine. It runs entirely on one Mac. Your prompt never leaves the machine.

## Five eras, one prompt

On a 16GB laptop we stacked:

- **2019** GPT-2  
- **2021** GPT-2 Medium  
- **2022** FLAN-T5 Large  
- **2023** Mistral 7B Instruct (4-bit)  
- **2024** Qwen2.5 7B Instruct (4-bit)

The honest claim on the tin: *a laptop-compatible sample of LLM history, not a verified record of who won each year.*

Then we actually ran it.

### “Explain mechanistic interpretability in AI”

2019 and 2021 never answer the question. They continue the *texture* of it — data points, “in the next section,” a fake Q/A that loops.

2022 tries. It explains “linguistic interpretability” and brings in physicists. Instruction tuning taught it to perform “explain,” not to know the field.

2023 defines it: internal mechanisms, causal chains of decisions. 2024 structures it more cleanly.

The jump from 2022 to 2023 is the whole product. You feel it before you analyze it.

### “The capital of France is”

Here progress is boring, which is the point.

2019 cannot stop repeating the prompt. 2021 says Paris and then loops anyway. 2022 answers with a single word: “Paris.” 2023 writes a tourism blurb. 2024 returns a clean sentence.

Newer is not automatically better for your task. A time machine that only shows fireworks is a marketing page.

### The crossword question

This one is from the stories people tell about when they started believing in scaling — a private, unpublished clue only a family member could know.

2019 invents a memoir about finding the puzzle on eBay.  
2022 answers **tadpoles**.  
2023 and 2024 refuse: I don’t have access to your grandmother’s crossword; anything I say would be guesswork.

The capability that shows up late isn’t omniscience. It’s *not making things up.*

## The bug the audit drawer caught

One of our first serious runs looked strange. The 2023 and 2024 models were confusedly asking for clarification about “a prompt.”

The models were fine. Our templates weren’t. A YAML escaping bug left the literal string `{prompt}` in the input instead of the question. Mistral and Qwen were eloquently discussing a placeholder token.

We only noticed because every trip stores the exact text each model received. The audit view isn’t a compliance checkbox. It’s how you tell “old model is weak” from “the harness is lying to you.” Fixed in one line of template, plus a regression test.

## What this does not show

It does not prove who had the best model in 2020. It does not put GPT-3 or GPT-5 on the timeline. Quantized 7B models are not the frontier. The early slots are stand-ins for bigger historical checkpoints we couldn’t fit.

What it does show is the shape of the climb: base models that can’t follow a request, instruction models that obey without understanding, chat models that finally do the work — and, on impossible questions, learn to say so.

Charts are useful after you already believe. For everyone else, there’s a text box, a few old weights, and five answers in a row.

---

*The local demo is open to inspect: frozen cohort, generation profile, adapters, and trip manifests. If a result looks wrong, don’t trust our summary — open the audit drawer and read what the model was actually given.*

# Translation quality screening

Completed outputs: 259; failed (output limit): 1.

This screening checks for generation problems and records a small manual review before interpreting the linguistic comparisons. Automatic flags identify passages to inspect; they are not error judgements.

## Automatic checks

- Stopped normally: 259 of 259.
- French function-word share > 5%: 1 (20153944).
- Repeated 6-grams (> 3 repeats): 7 (20154097, 20164070, 20203335, 20013164, 20023261, 20083550, 20163049).

### Review of flagged texts

The notes below are the saved human annotations.

- **20013164** (repetition): mirrors source. "États du sud et de l'est de la Méditerranée" appears twice in the French
- **20023261** (repetition): mirrors source. "mesures ... pour permettre aux détenus" repeated as in the French
- **20083550** (repetition): mirrors source. list of colourings repeated as in the French
- **20154097** (repetition): mirrors source. the French names "Message 2015 sur les constructions" four times (slightly varied wording); the output repeats one rendering
- **20163049** (repetition): mirrors source. "liste des mandats de gestion" passage repeated as in the French
- **20164070** (repetition): mirrors source. mercury thresholds and cadastre phrase repeated as in the French
- **20203335** (repetition): mirrors source. the French states the 1% tax on fortunes above 2 million twice (different wording); the output repeats one rendering
- **20153944** (French words): not untranslated. flag caused by an invented expansion of LIFD/LHID into French law names; no French passage

## Manual reading sample

The opening approximately 100 words of 20 randomly selected texts were reviewed (seed 2026). The categories and notes below reproduce the saved annotations; this is a sample review, not a full-document quality score.

| Recorded assessment | Texts |
|---|---:|
| No issue recorded | 10 |
| Minor issue | 5 |
| Content-changing issue | 5 |

- **20244110**: Minor issue. broken relative clause in second sentence; meaning recoverable
- **20133348**: No issue recorded
- **20254642**: Minor issue. concessive "Si" rendered as conditional "Wenn"
- **20223284**: No issue recorded
- **20073201**: Content-changing issue. "postulat" -> "Petition"; "LPP" -> "Rentenversicherungssystem"
- **20203069**: Minor issue. French abbreviations OFEV/CCE kept
- **20253316**: Minor issue. first sentence ungrammatical; "à l'horizon 2030" -> "im Jahr 2030"
- **20213158**: No issue recorded
- **20083138**: Content-changing issue. "Valais" -> "Waals" (Wallis); sentence structure garbled
- **20003094**: Minor issue. "pour seulement cinq jours d'exposition" omitted
- **20174092**: Content-changing issue. "poursuites" -> "Klagen" (Swiss term: Betreibungen); "émoluments" -> "Honorare"
- **20233852**: No issue recorded
- **20113806**: No issue recorded
- **20214097**: No issue recorded
- **20223224**: No issue recorded
- **20003435**: Content-changing issue. "145 milliards" -> "14,5 Milliarden"; "l'interdiction entre en vigueur" -> "Die Veröffentlichung erfolgt"
- **20133239**: No issue recorded
- **20063383**: Content-changing issue. parenthesis turned into a contradictory time clause ("als die Post ... 2006 bekannt gab")
- **20183432**: No issue recorded
- **20083928**: No issue recorded

## Annotation source

The original judgements and notes are in [screening_annotations.csv](../data/screening_annotations.csv).

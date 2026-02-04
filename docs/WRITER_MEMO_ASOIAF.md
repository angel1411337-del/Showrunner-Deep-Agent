# Writer Memo: Using Showrunner to Track ASOIAF Plot Trajectory

**Purpose**  
This memo translates the current system into practical uses for a writer or analyst re-reading the ASOIAF saga and trying to see where the plot is going. It assumes you are running the pipeline on your corpus and reviewing the generated outputs.

**What You Can Ask Right Now**
1. What are the unresolved plot threads, oaths, and prophecies?
2. Where are the strongest foreshadowing signals?
3. Which characters or factions are central based on mentions and relationships?
4. What events appear to drive the long-term direction of the story?
5. Which unresolved mysteries are most evidence-backed and likely to pay off?

**Primary Artifacts and What They’re For**
1. `out/exports/Unresolved_Threads_Dossier.md`  
Use this as your “open threads list.” It surfaces prophecies, mysteries, Chekhov’s guns, and plot threads with direct evidence anchors.
2. `out/obligations/obligations.json`  
Structured list of unresolved obligations with confidence scores and evidence anchor IDs.
3. `out/wiki/events.json`  
Rule‑based event extraction with provenance and time fields. Useful for reconstructing a high‑level timeline.
4. `out/wiki/relationships.json`  
Rule‑based relationships (alliances, enmities, kinship, oaths). Use this for power maps and shifting dynamics.
5. `out/kb/entities.json` and `out/kb/aliases.json`  
Canonical entity list and alias mapping. Use this to merge variant names and track character continuity.
6. `out/canon/passages.jsonl`  
The full passage store with stable IDs and text. Use this to verify claims and trace evidence.
7. `out/exports/mysteries_reveals_table.csv`  
Candidate reveals from the reveal planner. Use as a hypothesis list.
8. `out/exports/twist_bank.md`  
Speculative twist suggestions grounded in obligations and evidence anchors.

**How a Writer Can Use This in Practice**
1. Start with `out/exports/Unresolved_Threads_Dossier.md`.  
Read it like a writer’s “open loops list.” Highlight the top 10 that feel most narratively significant.
2. For each high‑value thread, open `out/canon/passages.jsonl` and pull the exact anchor text.  
This gives you the actual wording and tone so you can evaluate authorial intent.
3. Use `out/kb/entities.json` to track who is central to each thread.  
This helps you identify which POVs or houses are likely to be involved in future payoffs.
4. Cross‑check with `out/wiki/events.json` and `out/wiki/relationships.json`.  
This reveals whether the thread already connects to a known event or relationship shift.
5. Use `out/exports/mysteries_reveals_table.csv` as a hypothesis list.  
These are not “answers,” but plausible reveal paths rooted in evidence.
6. Write your own “Plot Trajectory Notes.”  
For each unresolved thread, note:  
`Thread → Evidence → Likely Character(s) → Likely Payoff Zone → Confidence`.

**How to Interpret the Time Fields**
1. `story_time` = in‑world timeline (what year/season in the story world)
2. `story_order` = narrative order (book/chapter sequence)
3. `created_at` = when the artifact was created in real time

Use `story_order` when you want “the author’s delivery order.” Use `story_time` for chronological reconstruction.

**Example Plot‑Trajectory Analysis (Template)**
1. Thread: “prince that was promised”  
2. Evidence: `book2:1` anchor excerpt  
3. Connected entities: `Azor Ahai`, `prophecy`, key POVs  
4. Relationship shifts: alliances forming around prophecy  
5. Likely payoff zone: final books conflict resolution  
6. Confidence: High (multiple anchors + repetition)

**Limits to Keep in Mind**
1. Event and relationship extraction is rule‑based and should be treated as a draft, not a final canon.
2. Obligations are heuristics; they are excellent for surfacing patterns but still need human judgment.
3. The system can surface evidence, not “truth.” The writer’s judgment is still the deciding filter.

**Recommended Routine**
1. Run the pipeline on the full saga.
2. Review the dossier weekly or after each reading session.
3. Keep a living list of “Top 20 unresolved threads.”
4. Use the wiki outputs to build your own thematic timeline and power map.

If you want, I can generate a companion “Plot Trajectory Memo” for a specific book subset, or a targeted report like “Jon + Bran + prophecy only,” using these outputs as the base.

# Proposed H2 subheadings — review draft

**Nothing here is live.** Every heading below is a *proposal*, written for Denise to approve, edit, or reject one by one. No prose has been changed and none is suggested for change — headings are purely additive, dropped between existing paragraphs.

**Why this exists.** Across 73 essays the corpus has 7 `<h2>` and 0 `<h3>`. The prose reads as continuous argument, which is a deliberate literary choice and reads beautifully. The cost is narrow and specific: AI answer engines (Google AI Overviews, ChatGPT search, Perplexity) extract *passages*, and they extract far more reliably when a passage sits under a descriptive heading that tells them where the idea begins and ends. Without headings they either quote the whole essay or guess at boundaries — usually badly, and usually from the opening paragraph rather than the passage that actually holds the argument.

**The rule I held myself to.** A heading that cheapens the prose is worse than no heading. Nothing here is a question stack, a listicle frame, or a keyword. Wherever possible the heading is lifted from her own words and images. Where an essay is one unbroken movement, I say so and recommend leaving it alone — four of the ten get that answer, and two of those are among the strongest pieces in the set.

**How to apply an approved heading.** Each row gives the exact heading text and the first ~8 words of the paragraph it should precede, so placement is unambiguous. To apply: in the `story.content` HTML, insert `<h2>Heading text</h2>` immediately *before* the `<p>` that begins with the quoted words. Nothing else moves. (Two essays — the gift guide and *On Ghosting* — need no new text at all; their headings already exist as `<strong>` labels and only need promoting to real `<h2>` tags. Those are the safest and highest-value changes in this document.)

**Summary of recommendations**

| Essay | Recommendation |
|---|---|
| How Cancer Raised Me | 4 headings |
| The Phobia | 4 headings |
| María Corina Machado and Venezuela's Fight for Freedom | 4 headings |
| New York is Where I Will Be From | 3 headings |
| Jagged Little Pill v. ¿Dónde Están los Ladrones? | 3 headings — promote her own existing labels |
| The Night Hope Returned | 3 headings |
| The Incurable Humanist's Holiday Gift Guide | promote existing labels — no new text |
| All the Way to the River… | **leave as-is** |
| On Ghosting | 3 headings — promote her own existing labels |
| The Voice You Ignore Until You Have No Choice | **leave as-is** |

Six essays get genuinely new headings. Three get their *own* existing in-text labels promoted to real headings (no invention at all). Two are recommended untouched.

---

## 1. How Cancer Raised Me

**Argument:** The sibling of a sick child learns to make herself small, and that learned smallness is its own grief — one she can only name now, decades later, as a survivor alongside her family rather than a victim of it.

This is the longest essay here (~3,550 words, 60 paragraphs) and the one where a reader — or a machine — is most likely to lose the thread. It already has two datelines of her own (*Caracas, Venezuela, August 2001* and *Caracas, Venezuela, February 2005*) doing heading-like work as plain paragraphs; two of the four proposals below simply honour that structure she already built.

| Proposed heading | Precedes paragraph starting… | Why the argument turns here |
|---|---|---|
| Caracas, Venezuela, August 2001 | *"Caracas, Venezuela, August 2001"* — promote this existing line itself to a heading | Her own dateline. The frame shifts from present-day reflection to the six-year-old's morning. She already marked this break; it's only tagged as body text. |
| Caracas, Venezuela, February 2005 | *"Caracas, Venezuela, February 2005"* — promote this existing line itself to a heading | Her second dateline. The relapse. "It seemed like a miracle" ends the first movement; this begins the one where the miracle is withdrawn. |
| The house became a germ-free zone again | *"Once again, our house became a germ-free zone. I saw…"* | The turn from medical event to domestic life-sentence. From here the essay stops being about her brother's illness and becomes about what the illness did to her childhood — the cancelled birthday guests, the declining grades, the forged signature. |
| I wanted to escape so badly | *"July finally arrived, and off to Lagonia I was…"* | The camp section is a self-contained ~1,200-word movement and the emotional climax. The child who has spent four years making herself small finally asks for something, gets it, and discovers the escape is worse than the house. Currently indistinguishable from the surrounding prose. |

*Note:* the two datelines are the highest-confidence changes in this essay — they require no new words at all, only a tag change.

---

## 2. The Phobia

**Argument:** A phobia is not "being scared" but a full-body occupation that shapes a life — and the thing that finally released her was not the therapy everyone prescribed but a strange man in Boston nobody would have recommended.

Three distinct movements already exist here: the anatomy of the fear, the failed cures, and the Mad Russian. The essay is ~3,470 words and the seam between "this is what my life was like" and "this is what I did about it" is currently invisible.

| Proposed heading | Precedes paragraph starting… | Why the argument turns here |
|---|---|---|
| How something like that begins | *"For the longest time, almost half the life I've already lived…"* | The frame closes on the dinner with Ale and opens on the Dobermann. Everything before is setup; everything after is the phobia itself. Her phrase, from the paragraph it introduces. |
| It isn't fear. It's a full-body occupation. | *"Stories like this go on and on. I fainted. I cried…"* | The accumulation of incidents stops and the essay turns analytical — the definition, the Healthline quote, the people who told her to calm down, *The Hound of the Baskervilles*, Anubis. This is the passage an AI engine would most want to cite on what a phobia actually is, and it currently has no boundary. |
| This couldn't go on | *"The tipping point came without warning but not without precedent…"* | Her own words. The white dog at the party at fourteen is the hinge of the essay: the fear stops being a condition she lives inside and becomes a problem she decides to solve. The all-night search, the name in the comment thread, the flight to Boston all follow from here. |
| The Mad Russian | *"And so, on February 12, 2010, we flew from Caracas to Boston…"* | The cure itself — Boston, the circle of chairs, the *poof*, the failed shelter test, the second session. A self-contained ~1,400-word passage and the single most citable thing in the essay. |

---

## 3. María Corina Machado and Venezuela's Fight for Freedom

**Argument:** Venezuela's collapse is not a left–right story but the twenty-six-year dismantling of a country's basic democratic machinery — told by someone who watched it from inside, lost her father to it, and now has to ask what her people will do with freedom when it comes.

This is the most structurally complex piece in the set: a personal frame, a long chronological history (1998→2025), and a closing moral argument. It is also the piece most likely to be queried by strangers ("what happened in Venezuela", "who is María Corina Machado") and most likely to be misquoted from the wrong paragraph. It benefits from headings more than anything else here.

| Proposed heading | Precedes paragraph starting… | Why the argument turns here |
|---|---|---|
| Serviam | *"Maria Corina Machado and I attended the same school…"* | The school motto — her word, and the word she returns to in the dedication. This is the personal passage on who Machado is and why she believes in her, distinct from both the disclaimer above it and the history below. |
| It was Sunday, December 6th, 1998 | *"It was Sunday, December 6th, 1998. It was a rainy day…"* | Her own sentence. The essay stops being personal testimony and begins the chronological account — the election, the Constituent Assembly, the ley habilitante, the recall, PDVSA, RCTV. This single break does the most work of any heading in the document: it separates "my story" from "the record." |
| What I saw at the museum | *"Since 1999, Venezuelan museums have been almost entirely dependent…"* | The long museum passage is a genuine digression — first-hand, art-world, and the origin of her master's thesis. It is the most distinctive thing in the essay and the least likely to be found, because it sits mid-timeline with no marker. |
| What will we do with our freedom? | *"But now comes the harder part: What will we do with our freedom?…"* | Her own question, and the essay's real turn — from record-keeping to moral argument. Everything after is about reconciliation, not history: those who stayed, those who left, resentment as a prison, "let us be peace-makers." A rare case where a question is right; it's hers, and it's the hinge. |

*Note on placement:* the `In memory of my father` dedication at the end should stay as it is — it is a closing inscription, not a section.

---

## 4. New York is Where I Will Be From

**Argument:** A seven-year-old's throwaway line becomes a life's mission statement; the city grants it, takes it back, and in taking it back teaches her the difference between wanting something and being willing to work for it.

Three clean movements: the dream, the collapse, the return. ~2,000 words, so it needs fewer headings than the long pieces — three is the right number and a fourth would chop it.

| Proposed heading | Precedes paragraph starting… | Why the argument turns here |
|---|---|---|
| The plan was flawless | *"My plan was flawless: Study. Intern. Use OPT…"* | Her own phrase, and her own irony — the next word is "Everything." The essay moves from childhood longing to the mechanics of actually trying, which is where it stops being a love letter and becomes a story. |
| Everything changed in the span of an email | *"Then came March 2020, and everything changed in the span of an email…"* | Her sentence. The Christie's closure is the plot's pivot — after it, every paragraph is loss: no OPT, empty grocery shelves, Apartment 3J, the ghosting, December 23rd. |
| I said: New York, I will be back | *"I'm writing this from New York. I made it back on October 3rd, 2022…"* | Her own line from the paragraph just above. The essay returns to the present and turns reflective — what the exile taught her, her father, the glass half empty, what home means. This is the passage worth quoting and it's currently buried as the last two paragraphs. |

---

## 5. Jagged Little Pill v. ¿Dónde Están los Ladrones?

**Argument:** Shakira's 1998 album is a Latin American answer to *Jagged Little Pill* — argued, deliberately, as a legal brief.

**This essay already has her headings.** She wrote it as a courtroom filing and marked the sections herself in all caps as `<strong>` inside plain paragraphs: **BACKGROUND**, **FACTS**, **FINAL MERITS OF DETERMINATION**. The conceit is the whole joke and the whole structure. Nothing needs inventing — these three only need promoting from `<p><strong>` to `<h2>`.

| Proposed heading | Precedes paragraph starting… | Why the argument turns here |
|---|---|---|
| BACKGROUND | *"BACKGROUND"* — promote this existing line itself | Her label. Opens the two-album history. |
| FACTS | *"FACTS"* — promote this existing line itself | Her label. Opens the exhibits, A through G — the body of the argument. |
| FINAL MERITS OF DETERMINATION | *"FINAL MERITS OF DETERMINATION"* — promote this existing line itself | Her label. Opens the concession-and-close: both artists are singular, here's the Glen Ballard coincidence, here's my verdict request. |

*Optional, only if she wants it:* the seven **EXHIBIT A–G** labels could become `<h3>`s. I'd lean against it — they're inline openings to paragraphs, not standalone sections, and seven headings in a 1,900-word essay would shred the rhythm. Three is enough. **Recommend: promote the three section labels only.**

---

## 6. The Night Hope Returned. Understanding What is Happening in Venezuela

**Argument:** For the first time in twenty-six years Venezuelans stayed awake with hope rather than fear — and the people telling them not to celebrate should listen to those who lived it before explaining it to them.

This is a dispatch, not a memoir: an opening scene, a rebuttal of outsiders' objections, a dossier on the regime, and a close. The rebuttal section is the reason the essay exists and is the passage most likely to be asked about.

| Proposed heading | Precedes paragraph starting… | Why the argument turns here |
|---|---|---|
| Please don't explain our own situation to us | *"People have reached out worried, stating that we shouldn't be celebrating…"* | Her own sentence, taken from later in the same movement. This is the turn from the 1:19 AM scene to the argument — "this situation requires looking beyond left-right divisions." Everything from here to the Panama paragraph answers an objection. |
| The ones still in the country | *"Let's not forget about the other key regime figures still in the country…"* | Her phrasing. The essay stops rebutting and starts documenting: Jorge Rodríguez, Padrino López, Cabello, then the oil collapse, the blackouts, the Cuban security detail. |
| A man who calls himself decent | *"The irony of Maduro calling himself 'decent' and 'innocent' is staggering…"* | The strongest passage in the piece and the most citable — 18,000 political prisoners, 10,000 tortured, the UN mission, $72 billion across 30 countries, $167 billion in debt. Currently it sits unmarked between a court-date paragraph and the closing appeal. |

---

## 7. The Incurable Humanist's Holiday Gift Guide

**Argument:** Gift-giving is an art you can learn — pay attention to the person, resist assumptions, and give what they wouldn't buy themselves.

**No new headings needed.** This essay is already fully structured — it just isn't *marked up* that way. Every section label exists as `<strong>` text inside a `<p>` or `<li>`, separated by `<hr>` rules. This is the single cleanest win in the document: pure markup change, zero editorial judgement, zero risk to the prose.

**Promote to `<h2>`:**

| Existing label | Currently |
|---|---|
| TIPS | `<p><strong>TIPS</strong></p>` |
| GIFT IDEAS | `<p><strong>GIFT IDEAS</strong></p>` |

**Promote to `<h3>` (the nine gift sections, all currently `<li><p><strong>…`):**

For the person who wants to journal · Personalized Stationery · A membership! · Anything from the MoMA Design Store · On a Budget · The host/hostess gift · A calendar for 2026 · Books! · For the one who's grieving · For the one who's far away

Two of these — **For the one who's grieving** and **For the one who's far away** — are the sections most likely to be surfaced by someone searching in genuine need, and they are the most deeply buried of the ten. That alone justifies the change.

*One caution:* the gift sections sit inside `<ol>` lists. Promoting them to `<h3>` means restructuring the list markup, which will change how the page looks. If that's a concern, promoting only **TIPS** and **GIFT IDEAS** to `<h2>` captures most of the benefit with no visual change at all. **Recommend: do the two `<h2>`s first; treat the `<h3>`s as a separate decision.**

---

## 8. All the Way to the River feels empty because what Elizabeth Gilbert describes is 'liquid love' marketed and packaged as 'solid love'

**RECOMMEND: leave as-is.**

**Argument:** Gilbert's memoir sells a six-month intensity binge as a great love, and in doing so diminishes the grief of people who have actually lost the solid kind.

This is a ~1,640-word critical essay in eleven paragraphs, and it is built as a single argumentative arc that cannot be cut without breaking: hesitation → summary of the book → "here is what I fundamentally disagree with" → the Bauman concept → "and then it hit me" → the verdict. The whole piece exists to deliver one sentence, which is also the title, and it arrives in paragraph ten. Every paragraph before it is load-bearing setup for that arrival.

A heading anywhere in the second half would pre-announce the conclusion and defuse the "and then it hit me" moment — which is the essay's only real turn and its entire rhetorical payoff. A heading in the first half would carve the book summary away from the objection it exists to enable.

There is also no citability problem to solve. The essay's key passage — the liquid/solid love definition and its application to Gilbert — is already clearly bounded by "I remembered the concept of 'solid love' and 'liquid love'" and "And then it hit me." Those sentences do a heading's work in her own voice, better than a heading would.

*If she disagrees and wants one break*, the only defensible place is before *"I am aware that this is Gilbert's story…"*, where summary ends and critique begins. A heading there would be something like **Where I fundamentally disagree** — her words. But I'd still argue against it.

---

## 9. On Ghosting

**Argument:** Being ghosted is its own form of grief — ambiguous loss, the person gone but not quite — and we tell the stories as comedy because without humour we'd spiral looking for answers that don't exist.

**Her headings already exist.** She structured this as three horror stories and labelled them herself: **Tale #1: The Beyoncé Story**, **Tale #2: The Irish Goodbye**, **Tale #3: Facade**. They're plain `<p>` text. Promoting them to `<h2>` is zero-invention and does real work — each tale is a self-contained 300–500-word narrative that currently has no machine-readable boundary at all.

| Proposed heading | Precedes paragraph starting… | Why the argument turns here |
|---|---|---|
| Tale #1: The Beyoncé Story | *"Tale #1: The Beyoncé Story"* — promote this existing line itself | Her label. First of three self-contained stories. |
| Tale #2: The Irish Goodbye | *"Tale #2: The Irish Goodbye"* — promote this existing line itself | Her label. Second story — and the best title of the three. |
| Tale #3: Facade | *"Tale #3: Facade"* — promote this existing line itself | Her label. Third story. |

*Considered and rejected:* a fourth heading before *"As humorous as these stories have become with time…"* — the closing turn where ghosting is named as ambiguous loss and Pauline Boss appears. It is genuinely the essay's thesis and the most citable passage in it. But it is only three short paragraphs, the last two of which are a sign-off, and a heading over a three-paragraph coda would look top-heavy against three long tales. The "Ghosts have their stories, too" landing works better unannounced. **If she wants it, "Ghosts have their stories, too" is the heading — her closing line.** My recommendation is the three tale labels only.

---

## 10. The Voice You Ignore Until You Have No Choice

**RECOMMEND: leave as-is. Do not touch this one.**

**Argument:** A father's life told in twenty-nine sentences, one per year of her life, from *when I was in my mother's womb* to *when I was twenty-six, we hugged for the last time* — and then what's left.

This is not an essay with sections. It is a litany. Twenty-nine paragraphs, each opening with the identical construction *"When I was [age], he…"*, each one or two sentences long, accumulating into a single unbroken movement. The form *is* the grief: the relentless year-by-year march is what makes "When I was twenty-six, we hugged for the last time. I didn't know it would be the last time" land the way it does. It only lands because nothing interrupted the count.

Any heading — anywhere — breaks the count. Put one in and the reader's eye stops, the rhythm resets, and the cumulative weight the form has been building for twenty-six years of sentences is dropped. There is no placement that doesn't do this damage. The final four paragraphs (grief, the wedding day, "Someday, you will understand") are a coda, and a heading before them would be the least-bad option, but "least-bad" is not a reason to do it.

This is also, at ~1,500 words, short enough to be extracted whole. The citability cost of leaving it alone is close to zero. The cost of subdividing it is the essay.

**Leave it exactly as she wrote it.**

---

## Notes on what I noticed

A few patterns, offered in case they're useful beyond these ten:

**She already writes her own headings — they're just not tagged as headings.** Four of the ten essays have explicit section labels sitting in plain body text: the two datelines in *How Cancer Raised Me*, the courtroom sections in *Jagged Little Pill*, the three tales in *On Ghosting*, and the entire label hierarchy in the gift guide. The fastest and least invasive improvement across the corpus is probably not "write new headings" but "find the labels she already wrote and mark them up properly." It would be worth scanning the other 63 essays for the same pattern before commissioning any new heading text.

**Her arguments turn at datelines and at sentences beginning "Then."** Almost every genuine structural break in these essays is marked by an explicit time-stamp — *It was Sunday, December 6th, 1998*; *And so, on February 12, 2010*; *Then came March 2020*; *At 1:19 AM on Saturday, January 3rd*. She is a chronological writer. Where a heading is needed, her own dated sentence is almost always the best source for it.

**The essays that resist headings are the ones with a single delayed payoff.** *The Voice You Ignore* and *All the Way to the River* both withhold their point until the end and depend on uninterrupted accumulation to get there. The essays that take headings well are the ones with genuinely separable movements — a history section, three discrete stories, a before-and-after. That's a reasonable test to apply to the rest of the corpus: *does this essay have parts, or does it have one motion?*

**Length is not the test; structure is.** The gift guide is one of the shortest pieces here and needs the most headings. *The Voice You Ignore* is a similar length and needs none.

---

## Verification note (added after drafting)

Two claims in this document were checked against the live corpus before it was
filed. One held, one needed qualifying.

**Held.** *On Ghosting* really does carry her own section labels — "Tale #1:
The Beyoncé Story", "Tale #2: The Irish Goodbye", "Tale #3: Facade" — sitting in
`<p><strong>` rather than `<h2>`. Promoting those is a markup fix, not
authorship, and is the safest change proposed here.

**Needed qualifying.** The suggestion that this pattern is widespread enough to
sweep across the other 63 essays does not survive contact with the data. A scan
for standalone `<p><strong>` blocks found only **4 essays, 23 blocks** — and
several are not headings at all. In *On Grief*, the matches are:

    "Listening to music."
    "Crying."
    "Watching a movie."

Those are emphasised items in a list about how grief arrives, not sections.
Auto-promoting them to `<h2>` would put a structural error into an essay about
her loss.

**Conclusion: do not automate this.** The pattern is real but inconsistent, and
the failure mode is a visible mistake in her writing rather than a silent one.
Each promotion should be eyeballed. The four candidates are:

| Essay | Blocks | Verdict |
|---|---|---|
| `the-incurable-humanists-holiday-gift-guide` | 13 | Genuine labels (TIPS, GIFT IDEAS) — promote the two top-level ones |
| `the-incurable-humanists-guide-to-hispanic-heritage-month` | 4 | Genuine labels (MUSEUMS & ART INSTITUTIONS:) |
| `on-grief` | 3 | **Not headings** — leave alone |
| `jagged-little-pill-v-donde-estan-los-ladrones` | 3 | Genuine labels (BACKGROUND/FACTS/FINAL MERITS) |

Plus `on-ghosting`, which uses a different markup shape and so did not match the
scan.

**One observation worth keeping.** Her arguments turn at datelines — "It was
Sunday, December 6th, 1998", "Then came March 2020", "At 1:19 AM on Saturday,
January 3rd". She is a chronological writer, and where a heading is genuinely
wanted, her own dated sentence is usually the best source for it.

### Applying an approved heading

Headings are additive; no prose changes. For each approved row, insert
`<h2>Heading text</h2>` immediately before the `<p>` that begins with the quoted
words, then update `story.content` in D1.

This is markup-only, so it will **not** move `content_hash` — that hashes
normalized text, not markup (see `content_hash` in `html_sanitize.py`) — and the
hourly Substack sync will keep short-circuiting rather than rewriting the row.
The same guarantee the srcset and `<h1>` migrations relied on. Assert it per row
before applying, as those migrations did.

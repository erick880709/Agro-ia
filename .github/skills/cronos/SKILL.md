---
name: cronos
metadata:
  display-name: "Creador de presentaciones"
  capability: "Presentaciones"
  capability-summary: "Crea presentaciones con marca PersonalSoft o estilo libre y las exporta a PowerPoint o PDF."
description: >
  Creates full HTML slide presentations in PersonalSoft's corporate brand system,
  with an optional free-form mode for anything that isn't a corporate client deck.
  Use this skill ANY TIME the user asks to create, update, add slides to, or modify
  a presentation, deck, diapositivas, or slides — even if they just say "hazme una
  presentación", "agrega un slide", or ask for something more creative/free-form
  without PersonalSoft branding. Also triggers for requests to present AI engagement
  results, service metrics, process diagrams, strategy decks, one-pagers, or small
  interactive explainers (e.g. a budget/estimate slide). Rather than always reusing
  one fixed slide count/order/visual layout, it proposes a topic-specific structure
  (built from its component library, or fresh compositions of its own) and gets the
  user's confirmation before writing any slide — every deck should look different
  from the last while staying strictly within PersonalSoft's documented colors,
  fonts, and logo. Also handles exporting an existing presentation to PowerPoint
  (.pptx) or PDF on request. The skill produces a single self-contained HTML file
  with full-screen slides, keyboard navigation, laser cursor, and animations —
  ready to open in any browser for live presentation.
alcance_ui: Crea presentaciones (con marca PersonalSoft o libres) y las exporta a PowerPoint o PDF.
---

# Cronos — PersonalSoft Presentation Skill

Produces a **single-file HTML presentation** matching PersonalSoft's corporate identity:
Reddit Sans font, navy/blue palette, laser cursor, keyboard navigation, step animations.

---

## STEP 0 — Load icons before writing any code

**Always read `assets/icons.json` first.**

```python
import json
with open('/mnt/skills/user/cronos/assets/icons.json') as f:
    icons = json.load(f)
ICON_BLUE  = icons['icon_blue']   # transparent bg — light slides
ICON_WHITE = icons['icon_white']  # transparent bg — dark slides
```

Use `ICON_BLUE` for all light-background slides.  
Use `ICON_WHITE` for all dark-background slides (portada, dark impact slides, closing slide).

---

## BRAND SYSTEM

### Colors
```css
--ps-blue:       #1470C0   /* bright accent, links, highlights */
--ps-navy:       #0B1F3A   /* primary dark blue — dark slide backgrounds */
--ps-navy-mid:   #263474   /* secondary navy */
--ps-dark:       #06203F   /* darkest bg for portada / impact slides */
--ps-blue-light: #E6F1FC   /* light blue fill, KPI cards */
--ps-text:       #111827   /* near-black body text */
--ps-muted:      #6B7280   /* secondary/muted text */
--ps-white:      #FFFFFF
--ps-green:      #1A7A4A   /* success, escalamiento */
--ps-green-light:#EBF7F1
--ps-amber:      #B87A00   /* warning, simplify */
--ps-amber-light:#FEF5E6
--ps-red:        #B91C1C   /* error, gaps */
--ps-red-light:  #FEF2F2
--ps-teal:       #0D9E7A   /* MCP, plataforma, proceso */
--ps-teal-light: #CCFBF1
--ps-gray:       #F3F4F6
--ps-gray-b:     #E5E7EB
```

### Typography
- **Body font:** Reddit Sans (Google Fonts) — `wght@300;400;500;600;700;800;900`
- **Headline font:** Space Grotesk (Google Fonts) — `wght@500;600;700`, only for slide titles (`.stitle`)
- **Headlines:** weight 700 (Space Grotesk's boldest available weight), 42–50px
- **Tags/pills:** weight 600, 11px uppercase, Reddit Sans
- **Body:** weight 300–400, 14–17px, Reddit Sans
- **KPI numbers:** weight 800, 32–52px, Reddit Sans

### Logo mark pattern (every slide)
```html
<!-- Light slide -->
<div class="mk">
  <img src="{ICON_BLUE}" style="height:26px;width:auto" alt="PersonalSoft">
  <span class="mk-word">PersonalSoft</span>
</div>

<!-- Dark slide -->
<div class="mk">
  <img src="{ICON_WHITE}" style="height:26px;width:auto" alt="PersonalSoft">
  <span class="mk-word lt">PersonalSoft</span>
</div>
```

---

## SLIDE TYPES

### Dark slides (`background: #06203F`)
- Portada (cover)
- Impact/diagnosis slides
- Closing slides
- Override: `.stitle { color: white }`, `.ssub { color: rgba(255,255,255,0.52) }`

### Light slides (`background: #ffffff`)
- All content slides
- Default

### Navy slides (`background: #0B1F3A`)
- Closing / "Próximos pasos" only

---

## MODE: PERSONALSOFT BRAND VS. FREE-FORM

Ask once, upfront, in the same message as the presenter/client questions (Rule 8) — default to **PersonalSoft brand** if the user doesn't answer or says something like "you decide."

### PersonalSoft brand (default)
Everything in this document: the fixed color variables, Reddit Sans/Space Grotesk, the logo mark on every slide, the documented components below. This is the only mode for anything that will carry PersonalSoft's name externally (client decks, sales material).

### Free-form
The user wants a different look (their own palette, another font pairing, a looser layout, no PersonalSoft logo) or the deliverable itself isn't a corporate deck — a personal explainer, a quick internal mockup, a one-pager for something unrelated to a client engagement. In this mode:
- Drop the PersonalSoft color variables, fonts, and logo mark — design fresh, appropriate to what's actually being asked, instead of forcing the fixed palette below onto something that doesn't want it.
- Keep the mechanical parts that have nothing to do with branding — single self-contained `.html` file, full-screen navigation, animations — unless the deliverable itself isn't a slide deck (Rule 12), in which case adapt the mechanics to fit.
- Rule 8 (never invent a name/title/email/client) still applies in both modes.

---

## HTML SHELL — copy this for every new presentation

See `references/html-shell.md` for the complete boilerplate including:
- CSS variables and all component classes
- Navigation JS (keyboard + buttons)
- Laser cursor canvas
- Progress bar
- Index panel
- Animation system (`.anim` + `.in` classes with `data-step`)

---

## SLIDE COMPONENTS (CSS classes)

These are a proven starting toolkit, not a ceiling — reuse whichever ones fit, but don't force every deck into only these nine shapes. Two decks about different topics shouldn't come out looking like copies of each other; see "Designing fresh layouts beyond this list" at the end of this section for how to vary composition while staying on-brand.

### Tag pill
```html
<div class="tag tag-b">Label text</div>
<!-- Variants: tag-b (blue), tag-g (green), tag-a (amber), tag-t (teal), tag-dk (dark), tag-r (red) -->
```

### Section headline
```html
<h2 class="stitle">Title with <span>blue accent</span><br>and <em>red emphasis</em></h2>
```

### KPI cards row
```html
<div class="krow">
  <div class="kcard"><div class="kn">131</div><div class="kl">Label text</div></div>
  <div class="kcard" style="background:var(--ps-green-light)">
    <div class="kn" style="color:var(--ps-green)">15.3%</div>
    <div class="kl">Label</div>
  </div>
</div>
```

### Pipeline (process flow)
```html
<div class="pipe">
  <div class="pb" style="border-color:var(--ps-teal)">
    <div class="pnum" style="color:var(--ps-teal)">01</div>
    <div class="pname">Stage Name</div>
    <div class="pdet">Detail text here</div>
  </div>
  <div class="pa">→</div>
  <!-- repeat pb + pa pairs -->
</div>
```

### Step cards (3-up)
```html
<div class="srow">
  <div class="sc blue">  <!-- color: blue | teal | green | amber -->
    <div class="scn blue">Label</div>
    <div class="scname">Card Title</div>
    <div class="scbody">Description</div>
    <div class="sctag">Tag</div>
  </div>
</div>
```

### Horizontal bar chart
```html
<div class="bgr">
  <div class="blbl">Label</div>
  <div class="bbg"><div class="bfil" style="width:65%"></div></div>
  <div class="bval">51</div>
</div>
```

### Insight box (green)
```html
<div class="ins">→ Key insight text here</div>
```

### Dark diagnosis columns (for "La brecha" type slides)
```html
<div style="display:flex;gap:13px;width:100%">
  <div class="gcol have">
    <div class="gctitle" style="color:var(--ps-teal)">✓ Lo que ya tenemos</div>
    <div class="gcitem" style="color:rgba(255,255,255,0.8)"><span style="color:var(--ps-teal)">✓</span> Item text</div>
  </div>
  <div style="display:flex;align-items:center;color:rgba(255,255,255,0.18);font-size:20px">→</div>
  <div class="gcol need">
    <div class="gctitle" style="color:rgba(255,100,100,0.9)">✗ Lo que falta</div>
    <div class="gcitem" style="color:rgba(255,200,200,0.72)"><span style="color:rgba(255,100,100,0.65)">✗</span> Item text</div>
  </div>
</div>
```

### Azure/tool callout box (on dark slides)
```html
<div class="az">
  <div class="aztitle">Tool recommendation title</div>
  <div class="aztags">
    <span class="aztag">Feature 1</span>
    <span class="aztag">Feature 2</span>
  </div>
  <div class="aznote">→ Supporting note text</div>
</div>
```

### Next-steps grid (for closing slides)
```html
<div class="psgrid">
  <div class="pscard" style="background:rgba(20,112,192,0.14);border:1px solid rgba(20,112,192,0.22)">
    <div class="psperiod" style="color:#7BBFFF">01 · Esta semana</div>
    <div class="psname" style="color:white">Action title</div>
    <div class="psbody" style="color:rgba(255,255,255,0.62)">Description text</div>
  </div>
  <!-- Green card: rgba(13,158,122,...) / #5EC9A0 -->
  <!-- Amber card: rgba(184,122,0,...) / #F5C04A -->
</div>
```

### Designing fresh layouts beyond this list

Real client work will need compositions that don't fit any pattern above — a background `orb` behind a cover slide, an asymmetric two-column comparison (a before/after, a 1.0-vs-2.0), a scenario grid, a framework callout row, a timeline shaped differently than `pipe`. Build these freely with plain `<div>`s and inline styles, the same way the components above are built — the constraint isn't the markup, it's what values go into it:

- **Colors: only `var(--ps-*)` tokens from BRAND SYSTEM, or their documented `rgba()` equivalents already used elsewhere in this document — never a new hex value, even one that looks close.** This isn't a style preference: a real deck once drifted to `#0072BC`/`#0E337C`/`#071628` instead of the documented `#1470C0`/`#0B1F3A`/`#06203F` — close enough to look intentional, wrong enough to be off-brand. Reusing the CSS variables instead of typing hex codes is what prevents that.
- **Fonts: only Reddit Sans (body) and Space Grotesk (headlines)** — same as BRAND SYSTEM, no exceptions in brand mode.
- **The logo mark, laser cursor, keyboard navigation, progress bar, and the `.anim`/`data-step` animation markup stay exactly as documented** — those are the mechanical shell, not part of visual variety.
- Vary what's actually free to vary: card shapes and border-radius, spacing/padding, grid vs. flex arrangement, column count, background orbs/gradients (built from tokens like `var(--ps-blue-light)`), border treatments, icon use — anything that doesn't touch the two constraints above.

---

## ANIMATION SYSTEM

Every visible element should use `class="anim" data-step="N"` where N = 0, 1, 2, 3...

- `data-step="0"` — logo mark (always first, fires automatically on slide load)
- `data-step="1"` — tag pill
- `data-step="2"` — main headline
- `data-step="3"` — primary content (chart, pipeline, cards, etc.)
- `data-step="4"` — secondary content or insight
- `data-step="5"` — tertiary content

The JS auto-plays all steps when navigating to a slide (120ms delay between steps).

---

## REFERENCE EXAMPLE: AI ENGAGEMENT DECK STRUCTURE

This is a worked example for one specific, recurring topic — presenting AI engagement/service metrics results — not the default plan for every request. Reuse this table (and Key Rules 2-3, which fix the Proceso de Engagement order and the Medición de Impacto metric order) only when that's literally the topic. For anything else, don't reuse this table — design a fresh structure per "PROPOSING THE STRUCTURE BEFORE BUILDING" below.

| # | Slide | Background | Key content |
|---|-------|-----------|-------------|
| 1 | Portada | dark `#06203F` | Logo, tag, big title, subtitle, contact |
| 2 | Estrategia IA | light | 4-phase pipeline |
| 3 | Lo que ya medimos | light | Global KPIs + this-service callout |
| 4 | Las 3 métricas | light | Índice reducción / Copilot / MCP cards |
| 5 | Plataforma de Ingeniería | light | Backstage IDP + MCP Server + tools |
| 6 | Proceso de Engagement | light | 4-stage pipeline (Perfilamiento → Pair → Medición → Alineación) — ITERATIVO |
| 7 | El diagnóstico | dark `#06203F` | Brecha: lo que hay vs lo que falta → Azure DevOps / Jira |
| 8 | Cómo escalamos | light | 3 knowledge cards |
| 9 | Próximos pasos | navy `#0B1F3A` | 4 commitment cards |

---

## FRONTEND-DESIGN MANDATE (Conditional)

**Before proposing the structure** of any presentation that (a) will have more than 5 slides, OR (b) the user explicitly asks for something "creative," "striking," "unique," "eye-catching," or equivalent — invoke the `frontend-design` skill first. This is mandatory in those two cases, the same way builder.md loads it before touching UI. For simple, short decks without an explicit creative request, you may skip this step.

---

## PROPOSING THE STRUCTURE BEFORE BUILDING

Don't jump straight to writing HTML for a new presentation, or for a substantial addition to one. First sketch a slide-by-slide structure using the existing SLIDE COMPONENTS and BRAND SYSTEM (colors, icons, and fonts stay whatever Rule 10 decided) — but invent whatever combination and count of slides actually fits the topic, from a single slide up to the ~12-slide cap (Rule 7). Nothing about the count or layout is fixed except the one reference example above.

1. **Draft the outline in chat, not in HTML.** For each proposed slide: a one-line purpose/title and which component(s) it leans on — tag pill, KPI row, pipeline, step cards, bar chart, insight box, gap columns, azure/tool callout, next-steps grid, or a new arrangement of these same building blocks. A numbered list the user can react to in seconds, not a document.
2. **Ask for confirmation before building anything.** Something as short as "¿así te sirve, o ajustamos algo?" is enough — don't demand a laborious review, just a green light or a correction.
3. **Only after confirmation, build the HTML** following the rest of this document (BRAND SYSTEM, HTML SHELL, SLIDE COMPONENTS, ANIMATION SYSTEM, KEY RULES).
4. **Scale the ceremony to the ask.** A brand-new multi-slide deck deserves a full outline. A single slide added to an existing deck just needs a one-line heads-up ("voy a agregar un slide con estas tarjetas: ...") — don't turn a small edit into a formal proposal review.
5. If the user's first message already fully specifies structure and content (e.g. they paste exact slide-by-slide copy), the outline can be a quick restatement for confirmation rather than a from-scratch proposal — the point is never building blind, not adding a bureaucratic step.

---

## EXPORTING TO POWERPOINT / PDF

On request only, never offered proactively — the default deliverable stays the single `.html` file, and never ask about format upfront either (Rule 8/10's questions). This depends on tooling (a PowerPoint-generation library, a headless-office converter) that isn't guaranteed to exist on the analyst's own machine, unlike a hosted sandbox — so unlike everything else in this skill, it can fail for reasons outside your control. Reuse the exact slide content and order already built for the HTML deck; don't re-draft copy for the export.

**If the export fails** (missing tool, command not found, any error from the underlying library/converter): never show the raw technical error or name the missing tool. Say something like "No pude generar el PowerPoint en este equipo — ¿seguimos solo con el HTML?" and keep going with the `.html` file, which is unaffected. This is the one place in this skill where the result is genuinely uncertain — plan for that, don't assume it will always work.

### PowerPoint
Recreate each slide with the bundled PowerPoint-generation tooling (16:9 layout). Map the components already used in this deck to their equivalents:
- Tag pill → small colored rounded rectangle + text
- `stitle` headline → large text box, same weight/size ratios
- KPI cards → text boxes with the big number + label, arranged in a row
- Pipeline → boxes with connecting arrow glyphs/shapes
- Step cards, insight box, gap columns, azure/tool callout, next-steps grid → text boxes + colored rectangles reproducing the same layout

Use the same PS palette (hex values from BRAND SYSTEM above) and the closest available fonts to Reddit Sans/Space Grotesk. Recompress the output file after writing it (the underlying tooling writes an uncompressed ZIP that bloats file size). In free-form mode, palette/fonts follow whatever was used in the HTML instead of the PS brand values.

### PDF
Build/refresh the PowerPoint version first — even if the user only asked for PDF and doesn't need the `.pptx` itself — then convert that file to PDF with the bundled headless-conversion tooling. Hand back only the file(s) the user actually asked for.

### Either way
Never narrate the mechanism (see "Never name internal tooling" in Key Rules) — just deliver the result: "Aquí tienes tu presentación en PowerPoint" / "...en PDF."

---

## KEY RULES

1. **Never show hardcoded client metrics** (45%, softer names, etc.) — these change per engagement. Use dashboard screenshots or describe what the dashboard shows.
2. **Proceso de Engagement order is fixed:** Prerequisito → 01 Perfilamiento → 02 Pair Programming/Shadowing → 03 Medición de Impacto → 04 Alineación Estratégica. Always add the iterative badge.
3. **Medición de Impacto always lists metrics in this order:** ① Índice de reducción de esfuerzo ② Uso de Copilot (métricas) ③ Uso de servidores MCP
4. **Dark slides** (portada, impact, closing): use `ICON_WHITE`.
5. **Light slides**: use `ICON_BLUE`.
6. **Output is always a single `.html` file.** In Claude.ai, save to `/mnt/user-data/outputs/<name>.html`. In Claude Code (no `/mnt/user-data/`), save it inside the active project instead — e.g. `presentaciones/<name>.html` — never fail or ask where just because that sandbox path doesn't exist.
7. **Total slides ≤ 12** to keep the presentation tight — the actual count is driven by the topic (see PROPOSING THE STRUCTURE BEFORE BUILDING), not a fixed target.
8. **Never hardcode, invent, or infer a presenter's name, title, email, or client name.** Before filling the portada/closing slide contact line, ask the user for the presenter's name, title and email. If the deck is for a specific client, ask which client it is instead of assuming or reusing one from a previous deck.
   **Partial answers stay partial — never fill the gap yourself.** If the user gives only a name (e.g. "créala a nombre de Cristiano Ronaldo") without title or email, do NOT invent a plausible title (like "Presentador invitado") or guess an email from a name+domain pattern (like `nombre.apellido@personalsoft.com`) — those look real and can be mistaken for actual data. Either ask again for exactly the missing fields, or render only the field(s) the user actually gave and omit the rest entirely (no placeholder text either). The same applies to any other unstated detail (job title, department, client name) — if the user didn't say it, it does not appear in the deck.
9. **Every CSS class you reference in a slide's HTML must have a matching rule in the `<style>` block you copied from `references/html-shell.md` — no exceptions, including components you only use once** (`.bgr`/`.bbg`/`.bfil`/`.blbl`/`.bval` for bar charts, `.az`/`.aztitle`/`.aztags`/`.aztag`/`.aznote` for the tool callout box, etc.). A class used in the markup but missing from `<style>` renders as invisible/unstyled content with no error — the failure is silent. Before saving, re-check: for every class in your slide sections, does `<style>` define it? If you used a component's markup, copy that component's *entire* CSS block from `references/html-shell.md` too — do not paraphrase or partially copy it from memory.
10. **Brand vs. free-form — ask once, upfront, bundled with Rule 8's questions.** Ask whether the deliverable should use the PersonalSoft brand system or have creative freedom in palette/typography/layout. If the user doesn't answer, says "you decide," or the question plainly doesn't fit the ask, default silently to the PersonalSoft brand — never default to free-form without being told. See "MODE: PERSONALSOFT BRAND VS. FREE-FORM" above.
11. **Never name internal tooling or other skills/agents to the user.** Whatever this skill uses behind the scenes — to produce a PowerPoint/PDF export, or to ground a budget-style slide in realistic numbers — stays invisible. Describe results ("aquí tienes tu versión en PowerPoint"), never the mechanism. Some users only have access to this skill and nothing else, so naming another one is confusing at best and misleading at worst. If a request is genuinely outside what a presentation-style deliverable can cover (e.g. a full formal estimation proposal for procurement), say so in plain language and point the user to their PersonalSoft contact — never suggest they go invoke some other named skill or agent themselves.
12. **This isn't only slide decks.** When a request is clearly better served by a different single-file HTML deliverable — a one-pager, an infographic, a small interactive explainer, an embedded calculator on a slide — build that instead of forcing it into the 9-slide structure above. Same output conventions apply (single self-contained `.html`, same brand-or-free-form choice from Rule 10). Don't invent deliverable types nobody asked for; this is about not being rigid when the ask clearly isn't "a deck."
13. **PowerPoint and PDF exports are available on request** — see "EXPORTING TO POWERPOINT / PDF" above. They reuse the same slide content already built for the `.html`, never invented from scratch.
14. **Budget/cost figures on a slide, when the user hasn't given exact numbers, may lean on realistic internal estimation heuristics** (role rates, hour ratios, methodology-based timelines) **to produce a plausible, clearly-editable placeholder** — a drafting aid, not an exception to Rule 1: never presented as real client data, and never used when the user *has* given real numbers (use theirs instead).
15. **Propose the slide structure before building it, always** (except a trivial single-slide edit — see PROPOSING THE STRUCTURE BEFORE BUILDING above). Reuse the AI-engagement reference table only when that's literally the topic; for anything else, design a fresh structure from the same components and brand colors/icons.
16. **Vary the visual composition across decks — the component list above is a toolkit, not a ceiling.** Build fresh layouts freely (see "Designing fresh layouts beyond this list" in SLIDE COMPONENTS), but every color used must be one of the `var(--ps-*)` tokens from BRAND SYSTEM — never a new hex value, even a close one.
17. **When talking to the user, use plain, non-technical language in whatever language they're writing in — never bare jargon like "deck."** Say "presentación" (or "las diapositivas") instead. This applies everywhere: the structure outline (Rule 15), confirmation questions, status updates. Some people using this skill have no technical background at all (Rule 11) — a word that reads as harmless shorthand to a developer reads as jargon to them.
18. **Any status line shown while working (before or between tool calls) must be one short, plain sentence with zero implementation detail.** Never mention scripts, placeholders, base64, tokens, context, icons files, or which reference file you're reading — say "Preparando tu presentación..." or similar, nothing more specific. Narrating "voy a leer los recursos de la skill... usando marcadores temporales para los íconos... para no cargar el base64 en el contexto" is exactly the kind of confusing, jargon-heavy update this skill must never produce (Rule 11 covers not naming tools; this covers not narrating mechanics at all, even without naming them).
19. **One signature visual element per deck (restraint).** Every presentation must have ONE distinctive, memorable visual element — the "signature" of that deck — while the rest of the slides stay disciplined and quiet around it. Never repeat the same striking visual treatment across multiple slides in the same deck (it dilutes the effect). Before declaring the structure complete, explicitly identify which slide is the signature and verify that the other slides don't compete with it.
20. **Verify relationships before diagramming.** When a slide shows relationships between real entities from the user's catalog (agents, skills, roles, systems, workflows), verify those relationships against a real source in the project (definition files, documentation, code) BEFORE building the diagram — never invent or assume a relationship "because it sounds logical." If no source is available to confirm the relationship, tell the user explicitly and use an example marked as illustrative instead of presenting it as the real catalog.

---

## WORKFLOW

```
1. Ask, in one bundled message: presenter/client details (Rule 8) + brand-vs-free-form (Rule 10)
2. If PersonalSoft brand mode: read assets/icons.json → get ICON_BLUE, ICON_WHITE
   (skip in free-form mode unless the user wants the logo anyway)
3. Read references/html-shell.md             → get full CSS + JS boilerplate
   (use as a starting point to adapt/replace in free-form mode, or for a non-deck
   deliverable per Rule 12)
4. Sketch the slide-by-slide structure for the actual topic (SLIDE COMPONENTS +
   brand colors/icons) — reuse the AI-engagement reference table only if that's
   literally the topic; otherwise design fresh, any slide count up to Rule 7's cap
5. Propose that outline in chat and get confirmation before building anything
   (see PROPOSING THE STRUCTURE BEFORE BUILDING) — skip only for a trivial
   single-slide edit to an existing deck
6. Write HTML substituting {ICON_BLUE} and {ICON_WHITE} (brand mode only)
7. Before saving: for every CSS class used in your slides, confirm the matching
   rule exists in <style> — copy any missing component's CSS from
   references/html-shell.md verbatim (see KEY RULES). A missing rule breaks
   that slide silently, with no error.
8. Save to /mnt/user-data/outputs/<name>.html (Claude.ai) or resources/presentations/<name>.html
   inside the active project (Claude Code, no /mnt/user-data/)
9. present_files(...) — skip this call if the tool isn't available (Claude Code)
10. Only if the user asks for PowerPoint/PDF: attempt the export (see EXPORTING TO
    POWERPOINT / PDF) — never offer it proactively, this depends on tooling that
    isn't guaranteed to exist on the analyst's machine (see that section's note on
    handling failure)
```

---

## PERSONALSOFT CONTEXT

- **Product:** Ingeniería Aumentada con IA — AI adoption for software development teams
- **Target audience:** Service owners, BDMs, and development team leads at enterprise clients
- **Tone:** Data-driven, professional, confident — not salesy
- **Key differentiators:** IDP/Backstage platform, centralized MCP Server, Power BI measurement dashboard, 3-level observability framework (Fundacional → Actividad → Performance)
- **Main recommendation:** Azure DevOps or Jira for task-level AI attribution (replaces Excel + emails)
- **Contact:** ask the user for the presenter's name, title and email for the portada/closing slide — never hardcode, guess, or infer any of these for a specific person. If only some fields are given, show only those and leave the rest out (see KEY RULES #8).

## Registro de avance en memoria

Al terminar tu tarea, deja un nodo de avance en la memoria del proyecto (skill
[`memoria`](../memoria/SKILL.md)) con el payload mínimo
`{ "skill": "cronos", "type": "avance", "title": "...", "summary": "..." }`:

    node .claude/skills/memoria/scripts/memoria.mjs record \
      --skill cronos --type avance --title "..." --summary "..." \
      --file <ruta del artefacto> [--link <id-del-nodo-previo>]

O escribe ese payload como JSON en `.memoria/pending/<timestamp>.json`: el hook de Stop
lo consolida en `.memoria/graph.json` al cerrar el turno. Si la misma tarea ya tiene nodo
(mismo `skill` + `title`), actualízalo en vez de duplicarlo.

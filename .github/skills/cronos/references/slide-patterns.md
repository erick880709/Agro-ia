# Slide Patterns Reference

Each section below gives the exact HTML pattern for that slide type.
Replace placeholder text; keep class names and structure.

---

## Portada (dark — #06203F)

```html
<section class="slide" id="s1" data-title="Portada" style="background:#06203F">
  <div class="orb" style="width:540px;height:540px;right:-150px;top:-150px;opacity:0.05;background:var(--ps-blue)"></div>
  <div class="orb" style="width:260px;height:260px;right:190px;bottom:-90px;opacity:0.04;background:var(--ps-blue)"></div>
  <div class="mk anim" data-step="0">
    <img src="{ICON_WHITE}" style="height:26px;width:auto" alt="PersonalSoft">
    <span class="mk-word lt">PersonalSoft</span>
  </div>
  <div class="tag tag-dk anim" data-step="1">Ingeniería Aumentada con IA · [Mes Año]</div>
  <h1 class="stitle anim" data-step="2" style="color:white">[Título principal]<br><span>[Subtítulo azul]</span></h1>
  <p class="ssub anim" data-step="3">[Descripción de la presentación en 1-2 líneas]</p>
  <div class="anim" data-step="4" style="margin-top:26px;padding:9px 15px;background:rgba(20,112,192,0.1);border:1px solid rgba(20,112,192,0.22);border-radius:9px;max-width:520px">
    <span style="font-size:11.5px;color:rgba(255,255,255,0.45)">[Nombre del presentador] · [Cargo] · [correo@personalsoft.com]</span>
  </div>
</section>
```

---

## Estrategia de Ingeniería Aumentada (light)

```html
<section class="slide" id="sN" data-title="Estrategia IA">
  <div class="orb" style="width:400px;height:400px;right:-90px;bottom:-90px;opacity:0.24"></div>
  <div class="mk anim" data-step="0"><img src="{ICON_BLUE}" style="height:26px;width:auto" alt="PersonalSoft"><span class="mk-word">PersonalSoft</span></div>
  <div class="tag tag-b anim" data-step="1">La estrategia detrás de la adopción</div>
  <h2 class="stitle anim" data-step="2" style="font-size:42px;margin-bottom:13px">Un modelo probado para ir<br>del uso a la <span>medición</span></h2>
  <div class="pipe anim" data-step="3">
    <div class="pb" style="border-color:var(--ps-teal)">
      <div class="pnum" style="color:var(--ps-teal)">Fase 1</div>
      <div class="pname">Activación</div>
      <div class="pdet">Kit de IA · GitHub Copilot · Pair Programming</div>
    </div>
    <div class="pa">→</div>
    <div class="pb" style="border-color:var(--ps-blue)">
      <div class="pnum" style="color:var(--ps-blue)">Fase 2</div>
      <div class="pname">Medición de Impacto</div>
      <div class="pdet">Índice de reducción · Copilot · Telemetría MCP</div>
    </div>
    <div class="pa">→</div>
    <div class="pb" style="border-color:var(--ps-navy)">
      <div class="pnum" style="color:var(--ps-navy)">Fase 3</div>
      <div class="pname">Escalamiento</div>
      <div class="pdet">Capacidad organizacional · Biblioteca de conocimiento</div>
    </div>
    <div class="pa">→</div>
    <div class="pb" style="border-color:var(--ps-green)">
      <div class="pnum" style="color:var(--ps-green)">Resultado</div>
      <div class="pname">Ingeniería Aumentada</div>
      <div class="pdet">Equipos autónomos · AI-driven en cada actividad</div>
    </div>
  </div>
  <p class="ssub anim" data-step="4" style="margin-top:14px;font-size:14.5px">No es adopción espontánea. Es un <strong style="color:var(--ps-text)">proceso estructurado</strong> donde cada fase mide su impacto y alimenta la siguiente.</p>
</section>
```

---

## Telemetría Global + Este servicio (light)

Muestra las métricas enterprise de Copilot a la izquierda, y los softers del engagement a la derecha.
Nunca hardcodear porcentajes de clientes específicos — esos van en los dashboards en vivo.

Key: left = "A nivel empresa" label | right = "En este servicio" label with "2" big teal number + softer name cards.

---

## Las 3 Métricas del Engagement (light)

Tres tarjetas `.sc` side by side:

| Card | Source | Color | Key content |
|------|--------|-------|-------------|
| 01 | Power BI | blue/navy | Fórmula: (Estimado − Ejecutado) / Estimado |
| 02 | GitHub Copilot | blue | LOC generadas/aceptadas, días activos, IDE, agentes |
| 03 | PersonalSoft IDP | teal | Prompts MCP más usados, solicitudes/softer, tendencia, alerta |

---

## Plataforma de Ingeniería (light)

3-column layout:
- **Col 1 (flex:1.2, border teal):** Backstage/IDP — Instructions, Skills, Resources, Agentes, Templates + URL `idp.personalsoft.com`
- **Col 2 (flex:1, border blue, bg blue-light):** MCP Server — prompts centralizados, acceso desde IDE, telemetría, curación CoE
- **Col 3 (flex:0.85):** Stack de herramientas — GitHub Copilot, Claude/Anthropic, Power BI (3 small cards)

---

## Proceso de Engagement (light) — ORDER IS FIXED, NEVER CHANGE

```html
<!-- FIXED ORDER — DO NOT MODIFY -->
<div style="display:flex;align-items:center;gap:12px;margin-bottom:10px" class="anim" data-step="1">
  <div class="tag tag-b">Proceso de Engagement de IA para los Servicios: Staffing</div>
  <div class="iter-badge">↻ Proceso iterativo</div>
</div>
<div class="pipe anim" data-step="2">
  <!-- 0: Prerequisito (blue bg) -->
  <div class="pb" style="border-color:var(--ps-blue);background:var(--ps-blue-light)">
    <div class="pnum" style="color:var(--ps-navy)">Prerequisito</div>
    <div class="pname" style="font-size:11px">Licenciamiento GitHub Copilot Empresarial</div>
    <div class="pdet" style="font-size:9px">+ Acuerdos de tiempo · Kit de IA</div>
  </div>
  <div class="pa">→</div>
  <!-- 01: Perfilamiento -->
  <div class="pb" style="border-color:var(--ps-teal)">
    <div class="pnum" style="color:var(--ps-teal)">01</div>
    <div class="pname">Perfilamiento Individualizado</div>
    <div class="pdet">IDE · Copilot previo · Asignación actual · Paradigma AI-driven</div>
  </div>
  <div class="pa">→</div>
  <!-- 02: Pair Programming -->
  <div class="pb" style="border-color:var(--ps-blue)">
    <div class="pnum" style="color:var(--ps-blue)">02</div>
    <div class="pname">Pair Programming / Shadowing</div>
    <div class="pdet">Acompañamiento especializado en vivo · No es clase · Es práctica real</div>
  </div>
  <div class="pa">→</div>
  <!-- 03: Medición — always list 3 sources in this order -->
  <div class="pb" style="border-color:var(--ps-navy)">
    <div class="pnum" style="color:var(--ps-navy)">03</div>
    <div class="pname">Medición de Impacto</div>
    <div class="pdet">① Índice de reducción (Power BI) &nbsp;② Copilot métricas &nbsp;③ Uso MCP</div>
  </div>
  <div class="pa">→</div>
  <!-- 04: Alineación Estratégica -->
  <div class="pb" style="border-color:var(--ps-green)">
    <div class="pnum" style="color:var(--ps-green)">04</div>
    <div class="pname">Alineación Estratégica</div>
    <div class="pdet">Engagement con el dueño del servicio para alinear expectativas</div>
  </div>
</div>
<!-- Observabilidad levels (always include) -->
<div class="anim" data-step="3" style="display:flex;gap:10px;margin-top:10px;width:100%">
  <div style="flex:1.8;padding:9px 12px;background:var(--ps-blue-light);border-radius:8px">
    <div style="font-size:9.5px;font-weight:700;color:var(--ps-navy);margin-bottom:3px">Observabilidad en 3 niveles</div>
    <div style="display:flex;gap:6px;margin-top:5px">
      <div style="flex:1;background:white;border-radius:5px;padding:5px 8px;text-align:center;border:1px solid var(--ps-gray-b)">
        <div style="font-size:9px;font-weight:700;color:var(--ps-teal)">Fundacional</div>
        <div style="font-size:9px;color:var(--ps-muted);margin-top:1px">Uso efectivo de IA</div>
      </div>
      <div style="flex:1;background:white;border-radius:5px;padding:5px 8px;text-align:center;border:1px solid var(--ps-gray-b)">
        <div style="font-size:9px;font-weight:700;color:var(--ps-blue)">Actividad</div>
        <div style="font-size:9px;color:var(--ps-muted);margin-top:1px">Adopción por tarea</div>
      </div>
      <div style="flex:1;background:white;border-radius:5px;padding:5px 8px;text-align:center;border:1px solid var(--ps-gray-b)">
        <div style="font-size:9px;font-weight:700;color:var(--ps-navy)">Performance</div>
        <div style="font-size:9px;color:var(--ps-muted);margin-top:1px">Reducción de esfuerzo</div>
      </div>
    </div>
  </div>
  <div style="flex:1;padding:9px 12px;background:var(--ps-gray);border-radius:8px">
    <div style="font-size:9.5px;font-weight:700;color:var(--ps-text);margin-bottom:3px">Kit de IA del servicio</div>
    <div style="font-size:10px;color:var(--ps-muted);line-height:1.5">MCP Server PersonalSoft · Instructions · Resources · Agentes · Skills por stack · El ciclo retroalimenta el kit en cada iteración</div>
  </div>
</div>
```

---

## El Diagnóstico / La Brecha (dark — #06203F)

Title formula: `"El proceso existe. La madurez para <em>ejecutarlo</em>, aún no."`

Two-column layout with `.gcol.have` (teal border) and `.gcol.need` (dashed border) + `.az` callout at bottom.

Key message in `.az`: Azure DevOps o Jira → team needs to move from **Fundacional** to **Performance**.

---

## Cómo Escalamos (light)

Three `.sc` cards:
- `blue`: Repositorio de conocimiento — base viva y accionable
- `teal`: Videos y FAQs — material desde engagements reales
- `green`: Soluciones reutilizables — lo que resuelve un equipo beneficia a toda la org

---

## Próximos Pasos (navy — #0B1F3A)

```html
<section class="slide" id="sN" data-title="Próximos pasos" style="background:#0B1F3A">
  <!-- icon white, mk-word lt -->
  <div class="tag anim" data-step="1" style="background:rgba(255,255,255,0.1);color:rgba(255,255,255,0.8)">Compromisos de esta reunión</div>
  <h2 class="stitle anim" data-step="2" style="font-size:48px;color:white">Lo que acordamos<br><span style="color:#7BBFFF">hoy</span></h2>
  <div class="psgrid anim" data-step="3">
    <!-- Blue card (this week / 2 weeks): background rgba(20,112,192,0.14), border rgba(20,112,192,0.22) -->
    <!-- Green card (today before leaving): background rgba(13,158,122,0.14), border rgba(13,158,122,0.3) -->
    <!-- Amber card (proposal / later): background rgba(184,122,0,0.14), border rgba(184,122,0,0.3) -->
  </div>
  <div class="anim" data-step="4" style="margin-top:14px;font-size:11.5px;color:rgba(255,255,255,0.28)">we make it happen · PersonalSoft</div>
</section>
```

Standard 4 commitments for an AI engagement closing:
1. Licencia GitHub Copilot (pendiente softer sin acceso) — Esta semana
2. Power BI por servicio (dashboard filtrado) — 2 semanas  
3. Acordar la métrica (¿tiempo o story points?) — Hoy antes de salir
4. Propuesta Azure DevOps / Jira — 2 semanas

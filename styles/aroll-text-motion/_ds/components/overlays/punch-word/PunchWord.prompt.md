PunchWord — the hero text beat: one bold word or short phrase that pops in over the strongest moment of a sentence, matching the "Sentence / Business / Decision" beats found in the reference A-roll cuts.

```jsx
<PunchWord eyebrow="The most expensive" text="Sentence" size="xl" />
<PunchWord text="Usually" size="md" align="left" />
```

Variants: `size` xl/lg/md for how dominant the word should feel; `underline` adds an accent stroke for a call-to-action feel; `align` controls placement within its safe zone. Words animate in one at a time (90ms stagger) via `ov-pop-in`.

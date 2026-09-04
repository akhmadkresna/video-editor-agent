ListCycle — a bold fixed word ("We do") next to a value that rotates through a list continuously, one item per beat.

```jsx
<ListCycle prefix="We do" items={["Brand identity","Lead generation","SEO"]} />
```

Auto-cycles on its own (every 1500ms by default — tune with `interval`) when `activeIndex` is omitted, matching the reference clip's self-advancing list; pass `activeIndex` to drive it manually from a timeline instead.

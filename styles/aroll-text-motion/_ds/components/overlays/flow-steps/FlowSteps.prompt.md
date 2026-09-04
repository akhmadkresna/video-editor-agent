FlowSteps — a chain of connected chips for explaining a process, funnel, or decision path as the voiceover walks through it.

```jsx
<FlowSteps steps={[{label:"Idea"},{label:"Test"},{label:"Launch"}]} activeIndex={1} />
```

Use `activeIndex` to fill in steps as the narration reaches them (drive with scroll/time in a real cut). `direction="vertical"` stacks steps for a narrower safe zone.

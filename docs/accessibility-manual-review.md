# LNG-013 Accessibility Manual Review Checklist

Automated checks in `playwright/a11y.spec.ts` cover layout, touch targets,
focus rings, basic color differentiation, and reduced motion at the code level.
The following require human device verification and are explicitly left open:

- [ ] Real-device test on physical iPhone SE (375px) and Android phone
- [ ] VoiceOver (iOS/macOS) and TalkBack (Android) screen-reader review
- [ ] WCAG 2.1 AA contrast audit with axe DevTools or Colour Contrast Analyser
- [ ] Keyboard-only navigation end-to-end on physical keyboard (macOS/Windows)
- [ ] Zoom to 200% — no content clipped or lost
- [ ] Landscape orientation at 375px height — no horizontal scroll

These items are tracked and will be closed in a follow-up accessibility audit session.

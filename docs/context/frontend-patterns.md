# Frontend Patterns Cheat-Sheet

- Component naming: PascalCase (`SectionCard.tsx`)
- Styling: Tailwind + `clsx` for conditional classes
- Animation: Framer Motion variants object in same file
- Icons: `lucide-react`
- State: React hooks only (no Redux in MVP)
- File structure:
  src/
    components/
      SectionCard.tsx
      Wizard.tsx
      Report.tsx
    hooks/
      useSSE.ts
    utils/
      cn.ts (clsx+twMerge)

# Component Style Guidelines

## Icons and Iconography

- Apply the shared icon sizing utilities (`size-icon-3xs` through `size-icon-3xl`) instead of hard-coded width/height values. These map directly to Vultr's 4px spacing grid.
- Use `size-icon-md` (24px) for default UI icons (navigation, buttons, form controls). Drop to `size-icon-sm` or `size-icon-xs` when space is tight, and jump to `size-icon-lg` through `size-icon-3xl` only for expressive hero moments or empty states.
- Functional icons should stay monochrome—inherit the current text color or set an explicit brand tone such as `text-vultr-blue`. Save gradients or multi-tone treatments for decorative artwork that supports the story.
- Pair icons with the `.icon` helper (inline-block + align-middle) or equivalent Tailwind utilities to keep them vertically aligned with nearby text.
- Never stretch, skew, or manually scale icons; always choose the closest preset to preserve geometry and visual rhythm.

## Buttons

### Base `.btn`

- Apply alongside a variant class to get the full treatment.
- Provides `inline-flex` layout with centered alignment, `gap-2`, and padding `px-5 py-3` for touch targets.
- Uses `rounded-[var(--radius-card)]`, the CTA text scale (`text-cta`, `leading-cta`), uppercase, and `font-semibold` typography.
- Includes accessible focus states via `focus-visible:ring-2 focus-visible:ring-vultr-light-blue focus-visible:ring-offset-2`.

### Variants

- `.btn-primary`: `bg-vultr-blue text-white` with subtle hover/active brightness shifts. Use for the primary action on a view.
- `.btn-outline`: `border border-vultr-blue bg-transparent text-vultr-blue`; fills blue with white text on hover. Ideal for secondary actions.
- `.btn-ghost`: `bg-transparent text-vultr-blue` with a translucent `hover:bg-vultr-sky-blue/40`. Works for tertiary or low-emphasis actions.
- `.btn-cta`: Extends the primary style and adds the `vultr-glow` halo to create a hero call-to-action. Use sparingly for the marquee action on marketing surfaces.

*Other historical button variants have been removed. Update components to rely on these four patterns so the brand system remains consistent in both light and dark themes.*

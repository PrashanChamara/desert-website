# ECB Concern Form 2026/27 — Design

## Goal

Let parents and players open and submit the ECB Concern Form from the existing `/tournaments` page, directly beneath the Tournament Season hero, while requiring a deliberate acknowledgement of the Academy's ECB tournament terms before the Google Form is made available.

## Chosen approach

Use the existing Desert Cubs modal pattern already used for tour and ECB registration forms. A new button, labelled **ECB Concern Form 2026/27**, opens a dedicated modal. The modal shows the Academy terms in a scrollable, accessible panel and a required acknowledgement checkbox. Once acknowledged, the user selects **Continue to the Concern Form** and the Google Form iframe loads lazily in the same popup.

This preserves the Google Form submission flow and avoids claiming that the website can inject terms into Google's cross-origin iframe before its native Submit button.

Google Form source: `https://docs.google.com/forms/d/e/1FAIpQLSeyjvE0itOx97iA7GWBal8LXnzhsvSlVd8D74EWgh3W1qLVvA/viewform?embedded=true`

## User flow

1. Visitor selects the new ECB Concern Form button in a standalone, always-visible CTA band immediately after the Tournament Season hero and before the conditional ECB National League registration section.
2. A branded, keyboard-accessible modal opens on the terms step.
3. Visitor reads the extracted Condition.pdf terms and checks the acknowledgement.
4. The continue control becomes available and switches the modal to the embedded Google Form.
5. The iframe receives its `src` only at that point; it has no source, request or prefetch beforehand. The visitor submits through Google's native form.
6. The form step shows a loading message until the iframe loads, offers a direct Google Form fallback link if it cannot load, and provides a return-to-terms control.
7. Close button, backdrop click and Escape close the modal and restore page scrolling. Closing before a Google Form submission may lose in-progress Google Form input.

## Scope

- Modify `templates/tournaments.html` for the feature and add focused regression coverage under `tests/`.
- Add a focused Flask rendering/regression test under `tests/`.
- Delete `Condition.pdf` only after its text is represented in the modal and tests pass.
- Preserve the existing ECB National League registration CTA, registration modal, tournament filters and page content in both visible and hidden registration states.

## Design and accessibility

- Use the established navy, gold and white palette, rounded modal card and existing `modal-overlay` styling.
- Render the terms as semantic headings, an ordered commitment list and a special-notes callout.
- Use a real checkbox with a visible label stating that acknowledgement grants access to, but does not submit, the Google form. Do not enable the continue control until it is checked.
- Use `role="dialog"`, `aria-modal`, an accessible title and description, a focus trap, and focus restoration to the opening button. Initial focus lands on the terms heading; on the form step, it lands on the form heading.
- Each modal open starts at the terms step with an unchecked acknowledgement, including after close/reopen. The acknowledgement is not persisted and is not analytics consent.
- On small screens, keep the card within the viewport; terms and form each scroll within the modal.

## Measurement and verification

- Track `ecb_concern_form_open`, `ecb_concern_terms_acknowledged`, and `ecb_concern_form_continue` using the existing `trackEvent` helper. Each carries only a static category and label; no terms acceptance or form data is sent to analytics.
- Automated checks assert button position, the exact Google form URL, faithful structured representation of every supplied PDF term, modal controls, consent gate and existing ECB registration preservation.
- Browser checks cover desktop and mobile opening; initial focus and Tab/Shift+Tab trapping; blocked continuation before consent; no iframe `src` or Google request before Continue; enabled continuation after consent; iframe loading; fallback-link visibility; return to terms; acknowledgement reset after close/reopen; Escape close; trigger-focus restoration; no overflow; and no console errors.

## Constraint

The Google iframe is controlled by Google and cannot be altered from this site. The terms gate is therefore intentionally presented before loading the iframe, rather than inside it.

## Terms source and retention

The user explicitly authorized deletion of `Condition.pdf` after its content has been faithfully represented in structured HTML. The source is not retained as a download because the popup terms become the published version. The published terms include all seven commitments and the U16/U19 National Pool special note from the PDF.

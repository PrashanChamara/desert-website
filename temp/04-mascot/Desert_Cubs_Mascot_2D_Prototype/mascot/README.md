# Desert Cubs mascot — transparent 2D motion prototype

This package preserves the supplied mascot artwork. It does **not** contain a .glb, a reconstructed 3D character, a skeletal rig, or production-approved animation. It is an honest, limited implementation of the brief's transparent-video alternative.

## Files

- assets/idle_loop.webm — 4 seconds, subtle breathing/body and fabric deformation.
- assets/walk_loop.webm — 1.25 seconds, approximate 2D stepping deformation. It is not a natural articulated walk and is not approved for production.
- assets/greeting_wave.webm — 3 seconds, localized raised-paw movement. Plays once in the preview.
- assets/flag_wave_loop.webm — 3 seconds, restrained fabric deformation to keep the supplied crest readable.
- assets/pause_idle.webm — 1 second, static resting illustration.
- assets/*.png — transparent posters/fallbacks.
- assets/manifest.json — dimensions, durations, state filenames and sizes.
- sources/ — original supplied reference artwork, unchanged.
- build.py — reproducible offline animation source (Python, Pillow, NumPy, SciPy and ffmpeg with libvpx-vp9).
- preview.html — local review page with state selector, light/dark backgrounds, pause, reduced-motion handling and hidden-tab pause.

## Review

Serve the folder over HTTP, e.g. `python -m http.server 8080`, then open http://localhost:8080/preview.html. Videos are 512 x 640 at 24 fps, with VP9 alpha and no audio. A good intended display size is approximately 200–280 CSS pixels tall. The 640-pixel canvas supports small mobile/desktop mascot placements. No libraries, remote fonts, or CDNs are needed in the preview.

For homepage integration, copy the assets folder and adapt the preview video/controller. Put it inside a fixed lower-right wrapper using `bottom: max(12px, env(safe-area-inset-bottom)); right: max(12px, env(safe-area-inset-right)); pointer-events: none;`. Reserve room for cookie banners, chat controls and navigation. Use the PNG poster when alpha-video playback is unsupported. Browser/device compatibility has not been tested; do not assume that a positive WebM codec check guarantees alpha support. Safari fallback is a static PNG in this package; no HEVC-alpha variant is provided.

## Remaining work before production

1. Build and approve a genuine 3D sculpt matching the head, eyes, smile, cap, uniform, shoes and tail. The source images alone do not define the hidden/back surfaces.
2. Retopology, UVs, baked fur detail, clean crest textures and optimized materials.
3. Bind a deforming skeleton; add eyelids/blink shapes, paw controls, tail and flag rig.
4. Author and review the five named animation clips, natural foot contacts and loop seams.
5. Export and validate a real animated GLB, then test target browsers and mobile performance.

The prototype has **no blinking**. It cannot turn in 3D, reveal unseen surfaces, or provide physically accurate limb motion. Idle/wave/walk use different supplied illustrations; transitions between states can change pose immediately. Within each clip there is continuous deformation, not a slideshow. Artwork is not a substitute for a 3D model and this package must not be described as one.

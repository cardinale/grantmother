# Grantmother kinetic-type film: shared bible (all sequence builders read this)

HARD CLOCK: now ~16:45. Every frame of your sequence must be on disk by **17:14**. Start your FINAL render no later than **17:05** whatever state the scene is in. If you are behind, simplify; never miss the clock. Render progressively (write frames as you go), so partial work still counts.

## Output contract
- 24 fps, 1920x1080, PNG RGB 8-bit. Film time t (seconds) -> global frame number f = round(t*24). Write each frame to
  `/Users/ac/Code/aws-hackathon/video/kinetic/frames/f_%05d.png` using the GLOBAL frame number (set scene.frame_start/end to your global range and render.filepath to `.../frames/f_` with use_file_extension; Blender pads to 4 digits by default, so set the path to `.../frames/f_#####`).
- Render ONLY your own frame range. Never write outside it. Your work dir: `/Users/ac/Code/aws-hackathon/video/kinetic/seq<X>/` (scene .py + .blend).
- The finished audio already exists (narration + music, 120 s): `/Users/ac/Code/aws-hackathon/video/build/mix.wav`. Word-level narration timings in film time: `/Users/ac/Code/aws-hackathon/video/build/word_times.json` (list of {line, word, t0, t1}). Sync every hero word to land ON its spoken t0 (fully arrived within 3 frames after t0).

## Look (same for everyone)
- Reference look: `/Users/ac/Code/aws-hackathon/video/blender/d3-kinetic/iter3.png`, built by `/Users/ac/Code/aws-hackathon/video/blender/d3-kinetic/scene.py` (copy its helpers freely: materials, make_text, the HUD text approach, bsp fracture for shatter, lights).
- World: neutral graphite #1c1c1e, floor #242426 slightly glossy, subtle depth haze. Borders/rules #3a3a3e. NO beige/cream/tan anywhere. No decorative colored edge strips.
- Hero type: 3D extruded, white (#f2f2f4), SF Pro Display Black (`/Library/Fonts/SF-Pro-Display-Black.otf`), small bevel; secondary type SF Pro Display Bold; HUD/annotation layer SF Pro Text Medium/Semibold small caps, flat, crisp, white or 60% gray, with thin rules.
- ONE accent: red #e5322b, reserved for the false claim ("2,000", "UNSUPPORTED"). Only sequence D uses red. Everyone else: white/gray only (sponsor logos keep their own colors).
- Sponsor logos: `/Users/ac/Code/aws-hackathon/video/assets/logos/final/<slug>-on-dark.png` (white versions for graphite) or `-on-light.png` on a white rounded chip. Use as emissive alpha planes. Never distort or recolor beyond the provided variants.
- Camera: 35-50 mm, low oblique angle so big type has perspective; always moving (slow dolly/orbit drift), fast whip/push on transitions. DOF on, motion blur on (shutter 0.5).
- Motion language: words SLAM in (drop/scale-in from depth with 2-4 frame overshoot), stack, get pushed out of frame by the next idea; camera flies through type. Exits are fast. Hard cuts on sentence boundaries are fine. Energy high but readable: each hero word holds >= 12 frames on screen.
- Spell everything exactly. No lorem/gibberish at readable sizes. On-screen numbers only story values: 3 schools, a 4th, $40k, 2,000 vs 600. The nonprofit story is illustrative.

## Render settings (speed matters: ~2,880 frames total are shared on one Apple M5 GPU with 5 other renders)
- BLENDER_EEVEE (Next), taa_render_samples 16, raytracing OFF unless your test shows < 0.5 s/frame with it, motion blur steps 1, volumetrics only if cheap (prefer a gradient world + mist pass faked by material).
- Test-render 3 frames first and time them. Target <= 0.6 s/frame while others render. If slower, cut samples/effects, not resolution.
- Blender: `/Applications/Blender.app/Contents/MacOS/Blender -b -P script.py`. Installed fonts only. Install nothing.
- Look at 2-3 of your rendered frames with the Read tool before the final render; fix legibility and composition.

## Return (<= 8 lines)
Frame range written (count actual files), seconds per frame, what each beat shows, anything missing.

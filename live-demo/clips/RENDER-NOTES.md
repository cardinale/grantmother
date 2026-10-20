# Masky render handoff — 2026-10-19

- Original avatar: You / 2TjfPM3IrnLiRTE56iyF / no voice or image.
- Created avatar: Grantmother Interviewer / Sedq2TZ5jdRq7vWOuohM / Warm American Female preset voice.
- The five clips use the graphic portrait variant recorded in ../assets/portrait-variant.json, pinned to conversation J1KqS5xoIa9RBv5IKgme. The avatar's original primary portrait is a different generated image; rerendering with prerender.py alone does not select the graphic variant. Use POST /conversations/{id}/avatar-image with the variant URL before rendering.
- Used equivalent prerender.py conversation/speak calls: five video turns plus two portrait generations, seven generation calls total. All five returned creditCost=0; portrait responses reported 0.005 + 0.015 credits. These are API-reported costs, not an independently audited account balance.
- q1.mp4 6.041667s; q2.mp4 4.041667s; q3.mp4 4.041667s; closer.mp4 4.041667s; hero-intro.mp4 15.000000s.
- hero-intro-masky-original.mp4 is the original 9.041667s Masky output. hero-intro.mp4 uses synchronized 0.75x speech/video playback, a 1s opening hold, and a closing hold to reach 15s. Spoken words are unchanged.
- All five deliverables have audio/video streams, pass full ffmpeg decoding, were frame-inspected, and loaded/played in the browser.
- config.js selects the new avatar and local portrait. LIVE_PERSONAL_CLOSER=false uses the local closing clip. index.html skips remote initialization when all four local clips exist and this flag is false.
- Verified http://localhost:8766/live-demo/ shows Masky clips loaded (4), with zero Masky API requests. No Masky UI action is needed for these files.
- Keep the credential-bearing config.js local; the submission/deck can use the MP4 files without credentials. Submission and deck publication remain the owner's separate work.

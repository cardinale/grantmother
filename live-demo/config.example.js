// Grantmother live opening: paste Masky credentials here, save, refresh the page.
// This file is served only on localhost. Do not commit a real key to a public repo.
window.GRANTMOTHER_CONFIG = {
  // From https://masky.ai/developer -> "Generate key" (starts with mky_),
  // or filled in automatically by: python3 live-demo/prerender.py
  MASKY_API_KEY: "",
  // Your interviewer avatar. Leave blank to use your first avatar.
  AVATAR_ID: "Sedq2TZ5jdRq7vWOuohM",
  // Optional still shown while the avatar is idle/listening (any public image URL).
  AVATAR_IMAGE_URL: "assets/grantmother-interviewer.jpg",
  // Ask Masky for a personalized spoken closing line ("Got it, <name>...") live on stage.
  // Audio turns take ~5-10 s; if slower than PERSONAL_TIMEOUT_MS the generic closing clip plays.
  LIVE_PERSONAL_CLOSER: false,
  PERSONAL_TIMEOUT_MS: 12000,
  // Typed-fallback defaults: Space (or Enter) with an empty answer box fills these.
  DEFAULTS: {
    name: "Anthony Cardinale",
    org: "Comfortist LLC",
    purpose: "Giving small nonprofits the power of a grant-writing team"
  },
  FILM_URL: "../out/grantmother-film.mp4",
  LINES: {
    q1: "Hi, I'm the Grantmother interviewer. Before we find you some money: what's your name?",
    q2: "Lovely to meet you. What's the name of your nonprofit?",
    q3: "And in one sentence, what does it do, and who does it help?",
    closer: "Got it. Let me show you how Grantmother handles the rest."
  }
};

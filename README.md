# Grantmother

**A grant office that refuses to lie.**

An AI-native grant-writing co-op for nonprofits too small to hire a grant writer.

**Anthony Cardinale · Brad Anderson · Comfortist LLC**
“Giving small nonprofits the power of a grant-writing team”

Universal Celebration Hackathon · AWS Builder Loft · October 19, 2026.

## What runs today

- **The live Masky voice-intake demo page:** an interviewer asks for a name, organization, and purpose; browser speech recognition or typed answers populate a fact sheet. Masky question clips can be pre-rendered for playback, with a live personalized closing line when credentials and service availability permit. Browser speech and typed input provide fallbacks. This is an intake demo, not a working grant-submission service.
- **The two-minute concept film:** illustrates the proposed company and its unsupported-claim review. The nonprofit, student counts, funding ask, and downstream workflow are illustrative, not measured outcomes. Download the film from the [hackathon release](https://github.com/cardinale/grantmother/releases/tag/v0.1).

The full six-agent pipeline is **proposed / in progress**. There is no claim here of completed funder discovery, independent model auditing, PromptQL orchestration, billing, grant awards, or deployment of the proposed build tools. Sponsor roles below describe intended responsibilities, not verified integrations.

## Six agents + one human

| Agent | Proposed responsibility |
| --- | --- |
| Interviewer | A **Masky** avatar conducts voice intake and captures a fact sheet. The founder confirms its contents. |
| Funder Scout | Uses **Glasser** to find foundations and program officers, with bounded, visible lookup costs. |
| Fit Checker | Checks eligibility, geography, budget size, nonprofit status, and deadlines; flags decisions for the founder. |
| Writer | Drafts a letter of inquiry and proposal sections from the approved facts and funder requirements. |
| Auditor | Runs on a different model from the Writer through **Flatkey**, classifies claim sources, and blocks unsupported claims for review. Independence is a design choice, not a guarantee against errors. |
| Treasurer | Uses **n8n** for deadlines, reminders, and sheet sync; **Flexprice** for funder-match metering and a proposed success tier. |

The **human founder** approves the fact sheet, selects funders, approves durable learnings, and signs the final application. Nothing is sent to a funder by the system. **PromptQL rooms and a human-approved wiki** are the proposed shared backbone. **Ask the W** defines the “agents do / humans decide” governance map.

## Sponsor roles

**Core:** PromptQL (rooms/wiki backbone), Masky (avatar interviewer), Glasser (funder discovery), Flatkey (Writer/Auditor model routing), n8n (operations), Flexprice (metering), Ask the W (governance).

**Build, proposed:** Snyk (code and agent-skill scanning), Prelint (review against the no-fabricated-facts specification), Tenki (sandbox/CI), CelestoAI (Scout development and testing sandbox).

See [the concept and sponsor matrix](docs/concept.md) for the original proposal and its explicitly labeled stretch ideas.

## Run the live demo

Requires Python 3 and a browser. Microphone input requires browser speech-recognition support and permission; typed answers remain available.

```sh
cp live-demo/config.example.js live-demo/config.js
```

Edit `live-demo/config.js`: add your Masky key to `MASKY_API_KEY`. The example retains the demo's `AVATAR_ID`; replace it with an avatar available to your account if needed. The key-bearing file is ignored by Git. Keep this a local demo: its browser configuration exposes the key to anyone who can access the server.

Small pre-rendered Masky question clips are included. After copying the example configuration, you can play those clips with the key left blank; the personalized closing line requires a live Masky connection.

To generate question clips for your own avatar, run the helper with your Masky account (this makes generation calls and may consume credits):

```sh
python3 live-demo/prerender.py
```

No credentials or generation are needed merely to inspect the source. Without Masky clips or an available connection, the page labels its browser-voice fallback. Empty answers can use the example configuration's sample defaults; those are demonstration values.

Download the `.mp4` from the [release](https://github.com/cardinale/grantmother/releases/tag/v0.1), put it in an ignored `out/` directory at the repo root, and set `FILM_URL` in your local configuration to `../out/<downloaded-filename>.mp4`. The sample defaults to `../out/grantmother-film.mp4`. Private release downloads require GitHub access.

From the repository root:

```sh
python3 -m http.server 8766
```

Open **http://localhost:8766/live-demo/**. For a server restricted to this machine, add `--bind 127.0.0.1` to the command above.

Keyboard controls: **Space** next step / accept answer; **Enter** submit typed answer; **F** film; **Esc** close film; **R** restart. Letter shortcuts are inactive while typing an answer.

## Submission materials and film credits

- `live-demo/`: intake page, credential-free example configuration, pre-render helper, and assets.
- `docs/concept.md`: Grantmother concept and the original sponsor matrix.
- `docs/film-bible.md`: kinetic film direction and production contract.
- `film/scripts/`: copied production scripts, including kinetic sequences as they become available. These are production-source snapshots, not a portable one-command film build: they retain original workspace/font paths and depend on production assets excluded from Git. Audio generation uses Gemini credentials from the environment; assembly requires Pillow and FFmpeg; kinetic sequences require Blender.
- `deck/`: pitch deck HTML and PDF. Open `/deck/` on the same local server.
- `assets/logos/`: sponsor PNG variants and provenance manifest. Logos belong to their respective owners; inclusion does not imply endorsement.

Film credits: **Blender kinetic type; Gemini TTS narration; Lyria 3.5 music.** The release identifies whether it contains the kinetic film or the earlier illustrated concept-film fallback.

Large films are distributed as release assets rather than Git blobs. Credentials, Blender binaries, frame sequences, build output, and oversized media are excluded. The repository is private; visibility is the owner's decision.

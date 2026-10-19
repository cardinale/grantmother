import os,json,urllib.request,urllib.error,base64,wave,concurrent.futures
from pathlib import Path
R=Path('/Users/ac/Code/aws-hackathon/video/audio')
STYLE='Warm, wry, youthful American female narrator for a handmade cut-paper animated film. A smile in the voice, knowing and playful, never salesy. Brisk but clear, natural pauses.'
LINES=[
 "Meet a founder. Three schools. Three counselors. And one very big ask: forty thousand dollars, for a fourth.",
 "Big foundations get pitched by professional grant writers. Tiny nonprofits get pitched by... whoever's still awake.",
 "So we built Grantmother: a grant office that small nonprofits share.",
 "It starts with a conversation. A Masky avatar interviews the founder, and every answer becomes the fact sheet the whole company is bound to.",
 "Glasser's scout finds the foundations that actually fund this work. A fit checker cuts the ones that don't. The founder picks.",
 "Then the Writer drafts the letter. And because writers get excited... it says: two thousand students.",
 "But the Auditor runs on a different model, through Flatkey, and checks every claim against the interview. The founder said six hundred. So... snip.",
 "Six hundred students. True. And still worth funding.",
 "Lessons go into a shared Prompt Q L wiki, only when the founder approves them. N eight N keeps the deadlines. Flexprice meters every funder match. And Ask the W draws the line between what agents do, and what humans decide.",
 "Nothing goes to a funder without the founder's own signature.",
 "Grantmother. A grant office that refuses to lie.",
]
def request(url,body):
 req=urllib.request.Request('https://generativelanguage.googleapis.com/v1beta/'+url,data=json.dumps(body).encode(),headers={'x-goog-api-key':os.environ['GEMINI_API_KEY'],'Content-Type':'application/json'})
 try:return json.load(urllib.request.urlopen(req,timeout=240))
 except urllib.error.HTTPError as e:raise RuntimeError(str(e.code)+' '+e.read().decode()[:800])
def tts(i):
 out=R/f'vo-{i:02d}.wav'
 if out.exists():return f'{out.name} exists'
 d=request('models/gemini-3.8-flash-tts:generateContent',{'contents':[{'role':'user','parts':[{'text':LINES[i],'speech_metadata':{'style':STYLE}}]}],'generationConfig':{'responseModalities':['AUDIO'],'speechConfig':{'voiceConfig':{'voice':'leda'}}}})
 part=next(p['inlineData'] for p in d['candidates'][0]['content']['parts'] if 'inlineData' in p);a=base64.b64decode(part['data'])
 if a[:4]==b'RIFF':out.write_bytes(a)
 else:
  with wave.open(str(out),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(a)
 (R/f'vo-{i:02d}-receipt.json').write_text(json.dumps({'model':d.get('modelVersion'),'usage':d.get('usageMetadata'),'text':LINES[i],'style':STYLE}))
 return out.name
def scan(x):
 if isinstance(x,dict):
  if 'data' in x and isinstance(x['data'],str) and len(x['data'])>1000:return x
  for v in x.values():
   a=scan(v)
   if a:return a
 elif isinstance(x,list):
  for v in x:
   a=scan(v)
   if a:return a
def music():
 out=R/'music.mp3'
 if out.exists():return 'music exists'
 prompt=('Two-minute INSTRUMENTAL original indie pop score for a handmade cut-paper animated film about a tiny nonprofit and an honest machine. No singing, no lyrics, no voices. '
  '100 BPM, lightly swung, warm and wry. Strummed ukulele and fingerpicked acoustic guitar, percussive upright piano, warm Rhodes, round upright bass, brushed drums, handclaps and finger snaps, glockenspiel and toy piano accents, a little whistled-style melody played on a melodica. '
  'Dry, intimate, live-in-the-room production with space for a spoken narrator. Structure: bright 8-second intro; light verse groove; around 0:45 a tension build with plucked strings; at about 0:55 a playful stop and a scissor-like snap, then a joyful lift; warm satisfying final chorus and a clean button ending at 2:00. Original melody, no reference to any existing song.')
 d=request('interactions',{'model':'lyria-3.5','input':prompt})
 a=scan(d)
 if not a:
  (R/'music-response.json').write_text(json.dumps(d)[:20000]);raise RuntimeError('no audio; keys '+str(list(d)))
 out.write_bytes(base64.b64decode(a['data']))
 (R/'music-receipt.json').write_text(json.dumps({'model':'lyria-3.5','prompt':prompt,'mime':a.get('mime_type',a.get('mimeType')),'id':d.get('id')}))
 return 'music ok'
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as p:
 jobs=[p.submit(music)]+[p.submit(tts,i) for i in range(len(LINES))]
 for j in concurrent.futures.as_completed(jobs):
  try:print(j.result(),flush=True)
  except Exception as e:print('ERROR',e,flush=True)

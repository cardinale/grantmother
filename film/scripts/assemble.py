import json, subprocess, os, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont, ImageFilter
V=Path('/Users/ac/Code/aws-hackathon/video'); S=V/'stills'; SH=S/'shots'; L=V/'assets/logos/final'; A=V/'audio'
B=V/'build'; B.mkdir(exist_ok=True); (V/'out').mkdir(exist_ok=True)
HERO=S/'d2-cutpaper.png'
FB='/System/Library/Fonts/Avenir Next.ttc'
def font(sz,bold=True): return ImageFont.truetype(FB,sz,index=(5 if bold else 7))  # 5=Bold? fallback below
def F(sz,w='bold'):
    for idx in ([5,0] if w=='bold' else [7,2,0]):
        try:
            f=ImageFont.truetype(FB,sz,index=idx); return f
        except Exception: pass
    return ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc',sz)
def logo(slug,h):
    im=Image.open(L/f'{slug}-on-light.png').convert('RGBA'); r=h/im.height
    return im.resize((max(1,int(im.width*r)),h),Image.LANCZOS)
def card(lines, slug=None, pos='bl', accent=None, big=False):
    W,H=1920,1080; ov=Image.new('RGBA',(W,H),(0,0,0,0))
    fs=[F(54 if big else 40,'bold'),F(30 if big else 28,'reg')]
    tw=max(ImageDraw.Draw(ov).textlength(t,font=fs[min(i,1)]) for i,t in enumerate(lines))
    lg=logo(slug,64) if slug else None
    pad=34; lw=(lg.width+28) if lg else 0
    cw=int(tw+lw+pad*2); ch=int(pad*2+sum((66 if (i==0 and big) else 50 if i==0 else 40) for i in range(len(lines))))
    ch=max(ch,(lg.height+pad*2) if lg else 0)
    x={'bl':80,'br':W-80-cw,'tl':80,'c':(W-cw)//2}[pos]; y={'bl':H-80-ch,'br':H-80-ch,'tl':80,'c':(H-ch)//2}[pos]
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle([x+6,y+10,x+cw+6,y+ch+10],22,fill=(0,0,0,70))
    ov=Image.alpha_composite(ov,sh.filter(ImageFilter.GaussianBlur(14)))
    d=ImageDraw.Draw(ov); d.rounded_rectangle([x,y,x+cw,y+ch],22,fill=(255,255,255,255),outline=(214,214,218,255),width=2)
    if lg: ov.alpha_composite(lg,(x+pad,y+(ch-lg.height)//2))
    ty=y+pad-4
    for i,t in enumerate(lines):
        col=(20,20,22,255) if i==0 else (90,90,96,255)
        if accent and i==len(lines)-1: col=accent
        d.text((x+pad+lw,ty),t,font=fs[min(i,1)],fill=col); ty+= (66 if (i==0 and big) else 50 if i==0 else 40)
    return ov
def save(ov,name): p=B/name; ov.save(p); return p
RED=(226,48,32,255)
def title_overlay():
    W,H=1920,1080; ov=Image.new('RGBA',(W,H),(255,255,255,0)); d=ImageDraw.Draw(ov)
    d.rectangle([0,0,W,H],fill=(255,255,255,150))
    t='Grantmother'; f=F(150); tw=d.textlength(t,font=f); d.text(((W-tw)/2,380),t,font=f,fill=(20,20,22,255))
    s='A grant office that refuses to lie.'; f2=F(48,'reg'); sw=d.textlength(s,font=f2); d.text(((W-sw)/2,580),s,font=f2,fill=(60,60,66,255))
    return ov
def end_card():
    W,H=1920,1080; im=Image.new('RGBA',(W,H),(255,255,255,255)); d=ImageDraw.Draw(im)
    def row(label,slugs,y,h):
        f=F(30,'reg'); lw=d.textlength(label,font=f); d.text(((W-lw)/2,y),label,font=f,fill=(90,90,96,255))
        ls=[logo(s,h) for s in slugs]; tot=sum(l.width for l in ls)+(44 if len(slugs)>5 else 60)*(len(ls)-1); x=(W-tot)//2
        for l in ls: im.alpha_composite(l,(x,y+60+(h-l.height)//2)); x+=l.width+(44 if len(slugs)>5 else 60)
    t='Grantmother'; f=F(84); tw=d.textlength(t,font=f); d.text(((W-tw)/2,90),t,font=f,fill=(20,20,22,255))
    row('Powered by',['promptql','masky','glasser','flatkey','n8n','flexprice','askthew'],260,52)
    row('Built with',['snyk','prelint','tenki','celesto'],480,60)
    f3=F(34,'bold'); s3='Anthony Cardinale · Comfortist LLC'; w3=d.textlength(s3,font=f3); d.text(((W-w3)/2,190),s3,font=f3,fill=(47,79,224,255))
    row('Universal Celebration Hackathon · AWS Builder Loft · October 19, 2026',['aws'],700,90)
    f=F(24,'reg'); s='Concept film. Nonprofit and figures are illustrative.'; sw=d.textlength(s,font=f); d.text(((W-sw)/2,990),s,font=f,fill=(120,120,126,255))
    return im
def img(name, fb=HERO):
    p=SH/name; return p if p.exists() else fb
# (image, dur, z0, z1, cx, cy, overlays[(png,t0,t1)])   cx,cy in 1920x1080 coords of the image
segs=[]
def seg(image,dur,z0,z1,cx,cy,ovs=()): segs.append(dict(image=str(image),dur=dur,z0=z0,z1=z1,cx=cx,cy=cy,ovs=list(ovs)))
hero_or=lambda n,*a: (img(n),)  # helper unused
s2=SH/'s02_founder.png'; s1=SH/'s01_wide.png'; s3=SH/'s03_proposal_draft.png'; s4=SH/'s04_scissors_cut.png'; s5=SH/'s05_600_close.png'; s6=SH/'s06_stickers.png'; s7=SH/'s07_schools.png'; s8=SH/'s08_topdown_clean.png'
E=lambda p: p.exists()
seg(s8 if E(s8) else HERO,6,1.12,1.0,960,540,[(save(title_overlay(),'ov_title.png'),0.6,6)])
seg(s2 if E(s2) else HERO,10,1.0,1.12,960 if E(s2) else 700,540 if E(s2) else 420,[(save(card(['Three schools. One big ask.','$40k for a fourth'],None,'br'),'ov_ask.png'),2.0,10)])
seg(s1 if E(s1) else HERO,11,1.05,1.15,960 if E(s1) else 1620,540 if E(s1) else 420)
seg(HERO,6.5,2.0,2.3,1585,985,[])
seg(s6 if E(s6) else HERO,10,1.4 if E(s6) else 2.2,1.6 if E(s6) else 2.5,960 if E(s6) else 1120,540 if E(s6) else 860,[(save(card(['Interviewer','Masky.ai avatar · voice intake to fact sheet'],'masky','tl'),'ov_masky.png'),0.5,10),(save(card(['Fact sheet — from the intake','Anthony Cardinale · Comfortist LLC','Giving small nonprofits the power of a grant-writing team'],None,'br'),'ov_fact.png'),2.5,10)])
seg(HERO,8.5,1.9,2.1,820,880,[(save(card(['Funder Scout','Glasser · foundations & program officers'],'glasser','tl'),'ov_glasser.png'),0.4,4.6),(save(card(['Fit Checker','Cuts mismatches · the founder picks'],None,'tl'),'ov_fit.png'),4.6,8.5)])
seg(s3 if E(s3) else HERO,8.5,1.5 if E(s3) else 1.9,1.7 if E(s3) else 2.2,960 if E(s3) else 900,540 if E(s3) else 300,[(save(card(['Writer','Drafted: “serves 2,000 students”'],None,'bl'),'ov_writer.png'),0.6,8.5)])
seg(s4 if E(s4) else HERO,11.5,1.0,1.35,1000,560,[(save(card(['Auditor · a different model via Flatkey','UNSUPPORTED — the intake said 600'],'flatkey','tl',accent=RED),'ov_auditor.png'),1.2,11.5)])
seg(s5 if E(s5) else HERO,6,1.4 if E(s5) else 2.4,1.6 if E(s5) else 2.7,960 if E(s5) else 790,540 if E(s5) else 455,[(save(card(['600 students.','True — and still worth funding.'],None,'br'),'ov_600.png'),0.5,6)])
seg(s6 if E(s6) else HERO,17,1.3 if E(s6) else 1.7,1.5 if E(s6) else 1.95,960 if E(s6) else 700,540 if E(s6) else 760,[
 (save(card(['Shared wiki','PromptQL · founder approves every learning'],'promptql','tl'),'ov_pql.png'),0.5,5),
 (save(card(['Deadlines & reminders','n8n'],'n8n','tl'),'ov_n8n.png'),5,8.6),
 (save(card(['Every funder match, metered','Flexprice'],'flexprice','tl'),'ov_flex.png'),8.6,12.2),
 (save(card(['Agents do · humans decide','Ask the W'],'askthew','tl'),'ov_askw.png'),12.2,17)])
seg(s7 if E(s7) else HERO,6,1.3 if E(s7) else 2.0,1.45 if E(s7) else 2.2,960 if E(s7) else 1700,540 if E(s7) else 640,[(save(card(['Nothing goes to a funder','without the founder’s signature.'],None,'bl'),'ov_sign.png'),0.4,6)])
seg(HERO,7,1.25,1.0,960,540,[(save(title_overlay(),'ov_title2.png'),0.8,7)])
end=B/'endcard.png'; end_card().save(end)
seg(end,12,1.0,1.0,960,540)
tot=sum(s['dur'] for s in segs); print('total',tot)
def render(i,s):
    out=B/f'seg{i:02d}.mp4'
    if out.exists(): return i,0,'cached'
    n=int(round(s['dur']*30)); W2,H2=3840,2160
    cx,cy=s['cx']*2,s['cy']*2
    z=f"({s['z0']}+({s['z1']}-{s['z0']})*on/{n})"
    x=f"max(0,min(iw-iw/zoom,{cx}-iw/zoom/2))"; y=f"max(0,min(ih-ih/zoom,{cy}-ih/zoom/2))"
    inputs=['-loop','1','-framerate','30','-i',s['image']]; fc=f"[0:v]scale={W2}:{H2},zoompan=z='{z}':x='{x}':y='{y}':d=1:s=1920x1080:fps=30,setsar=1[v0]"
    last='v0'
    for k,(png,t0,t1) in enumerate(s['ovs']):
        inputs+=['-loop','1','-framerate','30','-i',str(png)]
        fc+=f";[{k+1}:v]format=rgba,fade=t=in:st={t0}:d=0.25:alpha=1[o{k}];[{last}][o{k}]overlay=0:0:enable='between(t,{t0},{t1})'[v{k+1}]"; last=f'v{k+1}'
    cmd=['ffmpeg','-y','-v','error',*inputs,'-filter_complex',fc,'-map',f'[{last}]','-frames:v',str(n),'-c:v','h264_videotoolbox','-b:v','14M','-pix_fmt','yuv420p',str(out)]
    r=subprocess.run(cmd,capture_output=True,text=True)
    return i, r.returncode, r.stderr[-400:]
with ThreadPoolExecutor(6) as p:
    for i,rc,err in p.map(lambda a: render(*a), enumerate(segs)):
        print(i,rc,err)
(B/'list.txt').write_text(''.join(f"file 'seg{i:02d}.mp4'\n" for i in range(len(segs))))
subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(B/'list.txt'),'-c','copy',str(B/'video.mp4')],check=True)
# audio: VO starts
starts=[6.4,16.5,27.4,34.2,44.1,52.6,61.0,72.4,78.4,95.4,101.6]
vin=[]; fc=[]
for i,st in enumerate(starts):
    vin+=['-i',str(A/f'vo-{i:02d}.wav')]; fc.append(f"[{i+1}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(st*1000)}|{int(st*1000)},volume=1.6[a{i}]")
voe=' + '.join(f"between(t,{st},{st+0.15+float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(A/f'vo-{i:02d}.wav')]).decode())})" for i,st in enumerate(starts))
fc.append(f"[0:a]aresample=48000,atrim=0:{tot},volume='if({voe},0.22,0.6)':eval=frame,afade=t=out:st={tot-3}:d=3[m]")
fc.append(f"[m]{''.join(f'[a{i}]' for i in range(len(starts)))}amix=inputs={len(starts)+1}:normalize=0,alimiter=limit=0.95[aout]")
subprocess.run(['ffmpeg','-y','-v','error','-i',str(A/'music.mp3'),*vin,'-filter_complex',';'.join(fc),'-map','[aout]','-t',str(tot),'-c:a','pcm_s16le',str(B/'mix.wav')],check=True)
subprocess.run(['ffmpeg','-y','-v','error','-i',str(B/'video.mp4'),'-i',str(B/'mix.wav'),'-c:v','copy','-c:a','aac','-b:a','256k','-shortest','-movflags','+faststart',str(V/'out/grantmother-film.mp4')],check=True)
print('done')

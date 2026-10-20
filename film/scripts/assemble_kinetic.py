import os, subprocess, sys, shutil
from pathlib import Path
V=Path('/Users/ac/Code/aws-hackathon/video'); F=V/'kinetic/frames'; L=V/'build/klinks'
shutil.rmtree(L,ignore_errors=True); L.mkdir(parents=True)
N=2880; have=0; last=None; missing=[]
for f in range(N):
    p=F/f'f_{f:05d}.png'
    if p.exists() and p.stat().st_size>10000: last=p; have+=1
    else: missing.append(f)
    src=last if last else None
    if src: os.symlink(src,L/f'{f:05d}.png')
# leading gap: fill with first available
first=next((F/f'f_{f:05d}.png' for f in range(N) if (F/f'f_{f:05d}.png').exists()),None)
for f in range(N):
    if not (L/f'{f:05d}.png').exists() and first: os.symlink(first,L/f'{f:05d}.png')
runs=[];
for m in missing:
    if runs and m==runs[-1][1]+1: runs[-1][1]=m
    else: runs.append([m,m])
print(f'have {have}/{N}; missing runs (frames): {runs[:20]}')
out=V/'out/grantmother-kinetic.mp4'
subprocess.run(['ffmpeg','-y','-v','error','-framerate','24','-i',str(L/'%05d.png'),'-i',str(V/'build/mix.wav'),'-c:v','h264_videotoolbox','-b:v','16M','-pix_fmt','yuv420p','-c:a','aac','-b:a','256k','-shortest','-movflags','+faststart',str(out)],check=True)
print('wrote',out, subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(out)]).decode().strip())

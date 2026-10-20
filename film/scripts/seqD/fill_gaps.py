# Fill missing seqD frames with nearest earlier rendered frame (temporary; real renders overwrite).
import os, shutil, sys
D = "/Users/ac/Code/aws-hackathon/video/kinetic/frames"
filled = []
last = None
for f in range(1259, 1878):
    p = os.path.join(D, f"f_{f:05d}.png")
    if os.path.exists(p) and os.path.getsize(p) > 100000:
        last = p
    elif last:
        shutil.copyfile(last, p + ".tmp"); os.replace(p + ".tmp", p); filled.append(f)
print("filled", len(filled), filled[:3], filled[-3:])
open("/Users/ac/Code/aws-hackathon/video/kinetic/seqD/filled.txt", "w").write("\n".join(map(str, filled)))

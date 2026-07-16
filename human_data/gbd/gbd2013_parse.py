"""Parse the open Salomon 2015 GBD-2013 appendix (mmc1) into (health_state, lay_description, weight).
Weights come from Tables 2a/2b/3/4 (line ends with 'GBD2013 0.xxx (CI)'); lay descriptions
from Table 1, joined by health-state name. Text column shifts per page, so we split on runs
of >=2 spaces rather than a fixed column. Regenerates gbd2013_clean.csv from gbd2013_appendix.pdf
(requires poppler's pdftotext on PATH)."""
import csv, re, subprocess, tempfile
from pathlib import Path

D = Path(__file__).resolve().parent
PDF = D / "gbd2013_appendix.pdf"

with tempfile.TemporaryDirectory() as tmp:
    TXT = Path(tmp) / "gbd2013_appendix.txt"
    subprocess.run(["pdftotext", "-layout", str(PDF), str(TXT)], check=True)
    lines = TXT.read_text().split("\n")

SPLIT = re.compile(r"\s{2,}")
WEIGHT = re.compile(r"(\d\.\d{3})\s*\(")          # GBD2013 weight = first 'd.ddd ('
SKIP = re.compile(r"^\s*(Appendix Table|Health state|Lay description|Disability weight|"
                  r"estimate|uncertainty|interval|\d+\s*$|GBD 20|\(95)")
def norm(s): return re.sub(r"\s+", " ", s).strip().lower().rstrip(".")

def split2(line):
    parts = SPLIT.split(line.strip(), maxsplit=1)
    left = parts[0].strip()
    right = parts[1].strip() if len(parts) > 1 else ""
    return left, right

# boundaries
t1_end = next(i for i,l in enumerate(lines) if "Appendix Table 2a" in l and i>30)

# ---- Table 1: name -> lay description (leading indent => continuation) ----
desc = {}; cur=None
for l in lines[:t1_end]:
    if not l.strip() or SKIP.match(l):
        continue
    indent = len(l) - len(l.lstrip())
    if indent >= 20 and cur:          # indented = description continuation
        desc[cur] += " " + l.strip()
        continue
    left, right = split2(l)
    if left and right:                # new state (name + desc start)
        cur = left; desc[cur] = right
    elif left and not right:          # section header -> reset
        cur = None
desc_n = {norm(k): re.sub(r"\s+"," ",v).strip() for k,v in desc.items()}

# ---- Tables 2a/2b/3/4: name -> weight (first wins; dedup). Split inline desc (Table 4). ----
rows = {}
for l in lines[t1_end:]:
    m = WEIGHT.search(l)
    if not m or SKIP.match(l):
        continue
    field = l[:m.start()]
    hs, inline = split2(field)         # Table 4 glues name + lay desc before weight
    if not hs or len(hs) < 3:
        continue
    n = norm(hs)
    if n in rows:
        continue
    rows[n] = (hs, inline, float(m.group(1)))

# ---- join: prefer Table-1 desc, else inline (Table 4) desc, else name ----
out = []
for n,(hs,inline,w) in rows.items():
    if desc_n.get(n):   text, src = desc_n[n], "desc"
    elif inline:        text, src = inline, "inline"
    else:               text, src = hs, "name"
    out.append((hs, text, w, src))

with open(D/"gbd2013_clean.csv","w",newline="") as f:
    wr=csv.writer(f); wr.writerow(["health_state","lay_description","weight","text_source"])
    wr.writerows(out)

import numpy as np
w=np.array([r[2] for r in out]); nd=sum(1 for r in out if r[3]=="desc")
print(f"n={len(out)} states | {nd} with lay description, {len(out)-nd} name-only")
print(f"weight range {w.min():.3f}-{w.max():.3f} | distinct {len(set(w.round(3)))}")
print("\nsamples (text used for embedding):")
for r in out[:3]+out[len(out)//2:len(out)//2+3]+out[-3:]:
    print(f"  [{r[2]:.3f}] ({r[3]}) {r[1][:90]}")

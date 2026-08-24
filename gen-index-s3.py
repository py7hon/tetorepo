# gen_index.py
import os

INPUT = "files.txt"
OUTDIR = "out"

# key -> size
files = {}
folders = set()

with open(INPUT) as f:
    for line in f:
        parts = line.split()
        if len(parts) < 4:
            continue
        size = parts[2]
        key = parts[3]
        if key.endswith("index.html"):
            continue
        files[key] = size
        # register all parent folders
        parts_path = key.split("/")[:-1]
        acc = ""
        for p in parts_path:
            acc = f"{acc}{p}/"
            folders.add(acc)

folders.add("")  # root

def children(prefix):
    subfolders = set()
    subfiles = []
    plen = len(prefix)
    for key, size in files.items():
        if not key.startswith(prefix):
            continue
        rest = key[plen:]
        if not rest:
            continue
        if "/" in rest:
            subfolders.add(rest.split("/")[0] + "/")
        else:
            subfiles.append((rest, size))
    return sorted(subfolders), sorted(subfiles)

for prefix in folders:
    subfolders, subfiles = children(prefix)

    html = [f"<h1>Index of /{prefix}</h1>", "<ul>"]
    if prefix:
        html.append('<li><a href="../">../</a></li>')
    for d in subfolders:
        html.append(f'<li><a href="{d}">{d}</a></li>')
    for name, size in subfiles:
        html.append(f'<li><a href="{name}">{name}</a> ({size} bytes)</li>')
    html.append("</ul>")

    outpath = os.path.join(OUTDIR, prefix, "index.html")
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    with open(outpath, "w") as f:
        f.write("\n".join(html))

print(f"Generated {len(folders)} index.html files")
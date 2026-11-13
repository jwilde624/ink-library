# Build the Ink Library data + swatch bundles.
# usage: python3 -I build.py <view_rows.jsonl> <manifest.json> <swatch_webp_dir> <site_dir> <YYYY-MM-DD>
#  view_rows.jsonl : one JSON object per row from the Notion view "Public · Ink Library" (keys: id, Name, Brand,
#                    Color Category, Properties, Volume, Purchase Link, Inkings ...)
#  manifest.json   : {"<page id>": "<notion-file-block ref>" | "NONE"}
#  swatch_webp_dir : <page id>.webp crops (320x320) for any ids whose bundle entry should be (re)built
#  site_dir        : folder holding index.html and swatches/b-*.json (existing bundles are kept and updated)
import sys,json,re,os,glob,base64,html,io
from PIL import Image
rows_f,man_f,wdir,site,today=sys.argv[1:6]
rows=[json.loads(l) for l in open(rows_f) if l.strip()]
man=json.load(open(man_f))
C={'Pink':'p','Red':'r','Orange':'o','Yellow/Gold':'y','Green':'g','Teal/Turquoise':'t','Blue':'b','Purple':'u','Brown':'n','Gray/Black':'k'}
P={'Shimmer':'s','Sheen':'e','High-Shading':'h','Scented':'c','Pigment':'g'}
def clean(s):
    s=re.sub(r'<[^>]+>','',s or ''); s=html.unescape(s); s=re.sub(r'\\([\[\]\\*_#()`~>|-])',r'\1',s)
    return re.sub(r'\s+',' ',s).strip()
def arr(v):
    try: return json.loads(v) if v else []
    except Exception: return []
bpath=lambda k: os.path.join(site,'swatches',f'b-{k}.json')
os.makedirs(os.path.join(site,'swatches'),exist_ok=True)
B={k:(json.load(open(bpath(k))) if os.path.exists(bpath(k)) else {}) for k in '0123456789abcdef'}
# fold in new crops: centre band 320x150, webp q74
for f in glob.glob(os.path.join(wdir,'*.webp')):
    pid=os.path.basename(f)[:-5]
    im=Image.open(f).convert('RGB'); w,h=im.size; bh=round(w*150/320); top=(h-bh)//2
    buf=io.BytesIO(); im.crop((0,top,w,top+bh)).resize((320,150),Image.LANCZOS).save(buf,'WEBP',quality=74,method=6)
    B[pid[-1]][pid]='data:image/webp;base64,'+base64.b64encode(buf.getvalue()).decode()
ids={r['id'] for r in rows}
for k in B: B[k]={i:v for i,v in B[k].items() if i in ids}   # drop removed inks
have={i for k in B for i in B[k]}
out=[]
for r in rows:
    out.append([clean(r.get('Name')),clean(r.get('Brand')),''.join(C[c] for c in arr(r.get('Color Category')) if c in C),
        ''.join(P[p] for p in arr(r.get('Properties')) if p in P),{'Bottle':'B','Sample':'S'}.get(r.get('Volume') or '',''),
        (r.get('Purchase Link') or '').strip(),len(arr(r.get('Inkings'))),r['id'] if r['id'] in have else ''])
data=json.dumps({'updated':today,'inks':out},ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
p=os.path.join(site,'index.html'); h=open(p).read()
m=re.search(r'(<script id="ink-data" type="application/json">)(.*?)(</script>)',h,re.S)
h=h[:m.start(2)]+data+h[m.end(2):]; open(p,'w').write(h)
for k in B: json.dump(B[k],open(bpath(k),'w'),separators=(',',':'))
tot=sum(os.path.getsize(bpath(k)) for k in B)
print(f'{len(out)} inks, {len(have)} with swatch photos, {len(out)-len(have)} without; bundles {tot/1e6:.2f} MB')
missing=[r['id'] for r in rows if r['id'] not in man]
print('ids not in manifest:',len(missing))

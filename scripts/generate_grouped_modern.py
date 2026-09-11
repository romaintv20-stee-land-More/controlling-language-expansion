import zipfile, json, glob, os, hashlib, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'build'/'modern'
OUT=ROOT/'build'/'grouped-modern'
VERSION='1.0.0-test2'
MOD_ID='controllinglanguageexpansion'
OUT.mkdir(parents=True, exist_ok=True)
for p in OUT.glob('*'): p.unlink() if p.is_file() else shutil.rmtree(p)

GROUPS = [
    ('1.13.2-1.14.2', ['1.13.2','1.14.2'], {'pack_format':4}),
    ('1.15', ['1.15'], {'pack_format':5}),
    ('1.16', ['1.16'], {'pack_format':6}),
    ('1.17', ['1.17'], {'pack_format':7}),
    ('1.18', ['1.18'], {'pack_format':8}),
    ('1.19', ['1.19'], {'pack_format':9}),
    ('1.19.3', ['1.19.3'], {'pack_format':12}),
    ('1.19.4', ['1.19.4'], {'pack_format':13}),
    ('1.20-1.20.4', ['1.20','1.20.1','1.20.2','1.20.3','1.20.4'], {'pack_format':15,'supported_formats':[15,22]}),
    ('1.20.5-1.21.8', ['1.20.5','1.20.6','1.21','1.21.1','1.21.2','1.21.3','1.21.4','1.21.5','1.21.6','1.21.7','1.21.8'], {'pack_format':32,'supported_formats':[32,64]}),
    ('1.21.9-26.2', ['1.21.9','1.21.10','1.21.11','26.1','26.1.1','26.1.2','26.2'], {'min_format':[69,0],'max_format':[88,0]}),
]

def jar_for(v):
    files=list((SRC/v).glob('*.jar'))
    if len(files)!=1: raise RuntimeError((v,files))
    return files[0]

def read_payload(jar):
    out={}
    with zipfile.ZipFile(jar) as z:
        for n in z.namelist():
            if n.startswith('assets/controlling/lang/') and n.endswith('.json'):
                loc=Path(n).stem
                data=json.loads(z.read(n).decode('utf-8'))
                out[loc]=data
    return out

def merge_payload(versions):
    merged={}
    provenance={}
    conflicts=[]
    for v in versions:
        for loc, data in read_payload(jar_for(v)).items():
            m=merged.setdefault(loc,{})
            for k,val in data.items():
                if k in m and m[k]!=val:
                    conflicts.append((loc,k,m[k],val,provenance[(loc,k)],v))
                else:
                    m[k]=val
                    provenance.setdefault((loc,k),v)
    if conflicts:
        raise RuntimeError(f'Payload conflicts: {conflicts[:10]}')
    return merged, provenance

def copy_classes(source):
    with zipfile.ZipFile(source) as z:
        return {n:z.read(n) for n in z.namelist() if n.endswith('.class') and n.startswith('com/steelandmore/')}

def metadata(range_label, pack_meta):
    manifest=(
        'Manifest-Version: 1.0\n'
        'Implementation-Title: Controlling Language Expansion\n'
        f'Implementation-Version: {VERSION}\n'
        f'Built-For-Minecraft: {range_label}\n\n'
    )
    mods=f'''modLoader="javafml"
loaderVersion="[25,)"
license="MIT"
issueTrackerURL="https://github.com/romaintv20-stee-land-More/controlling-language-expansion/issues"
displayURL="https://github.com/romaintv20-stee-land-More/controlling-language-expansion"
authors="Steel-and-More"

[[mods]]
modId="{MOD_ID}"
version="{VERSION}"
displayName="Controlling Language Expansion"
description="Unofficial localization expansion for Controlling."

[[dependencies.{MOD_ID}]]
modId="controlling"
mandatory=true
versionRange="[4.0.0,)"
ordering="AFTER"
side="CLIENT"
'''
    neo=f'''modLoader="javafml"
loaderVersion="[1,)"
license="MIT"

[[mods]]
modId="{MOD_ID}"
version="{VERSION}"
displayName="Controlling Language Expansion"
authors="Steel-and-More"
description="Unofficial localization expansion for Controlling."
'''
    fabric={
        'schemaVersion':1,'id':MOD_ID,'version':VERSION,
        'name':'Controlling Language Expansion',
        'description':'Unofficial localization expansion for Controlling.',
        'authors':['Steel-and-More'],'environment':'client',
        'depends':{'minecraft':'*'},'suggests':{'controlling':'*'}
    }
    pm={'pack':dict(pack_meta,description=f'Controlling Language Expansion for Minecraft {range_label}')}
    return manifest,mods,neo,json.dumps(fabric,ensure_ascii=False,indent=2)+'\n',json.dumps(pm,ensure_ascii=False,indent=2)+'\n'

report=[]
for label,versions,packmeta in GROUPS:
    merged,prov=merge_payload(versions)
    classes=copy_classes(jar_for(versions[0]))
    dest=OUT/f'Controlling-Language-Expansion-{VERSION}-mc{label}.jar'
    manifest,mods,neo,fabric,pack=metadata(label,packmeta)
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('META-INF/MANIFEST.MF',manifest)
        z.writestr('META-INF/mods.toml',mods)
        z.writestr('META-INF/neoforge.mods.toml',neo)
        z.writestr('fabric.mod.json',fabric)
        z.writestr('pack.mcmeta',pack)
        for n,b in classes.items(): z.writestr(n,b)
        for loc in sorted(merged):
            ordered=dict(sorted(merged[loc].items()))
            z.writestr(f'assets/controlling/lang/{loc}.json',json.dumps(ordered,ensure_ascii=False,indent=2)+'\n')
    with zipfile.ZipFile(dest) as z:
        bad=z.testzip()
        if bad: raise RuntimeError(f'{dest}: corrupt {bad}')
        json.loads(z.read('pack.mcmeta'))['pack']
        for n in z.namelist():
            if n.endswith('.json'): json.loads(z.read(n))
    sha=hashlib.sha256(dest.read_bytes()).hexdigest()
    entry_count=sum(len(x) for x in merged.values())
    report.append({'label':label,'versions':versions,'locales':len(merged),'entries':entry_count,'bytes':dest.stat().st_size,'sha256':sha,'pack':packmeta,'file':dest.name})

vs=GROUPS[-1][1]
hashes=[]
for v in vs:
    payload=read_payload(jar_for(v))
    canonical=json.dumps(payload,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
    hashes.append((v,hashlib.sha256(canonical).hexdigest()))
if len({h for _,h in hashes})!=1:
    raise RuntimeError('Expected identical payloads for 1.21.9-26.2')

(OUT/'GROUPED_BUILD_REPORT.json').write_text(json.dumps({'version':VERSION,'jar_count':len(report),'groups':report,'late_payload_hashes':hashes},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
zipout=OUT/'Controlling-Language-Expansion-Grouped-Test-JARs-1.13.2-to-26.2.zip'
if zipout.exists(): zipout.unlink()
with zipfile.ZipFile(zipout,'w',compression=zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.glob('*.jar')): z.write(p,p.name)
    z.write(OUT/'GROUPED_BUILD_REPORT.json','GROUPED_BUILD_REPORT.json')
print(json.dumps(report,indent=2,ensure_ascii=False))
print('ZIP',zipout,zipout.stat().st_size)

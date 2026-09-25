#!/usr/bin/env python3
"""Adapt Beyond & More's Minecraft 26.1.2 Marathi translations to official 26.3."""
from __future__ import annotations
import argparse
import concurrent.futures
import hashlib
import json
import re
import threading
import time
import unicodedata
import urllib.parse
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_BM=Path(r"D:\ssd\Autres\Mcreator\Mods\Steel_and_More\src\main\resources\assets\minecraft\lang\mr_in.json")
TOKEN=re.compile(r"%(?:\d+\$)?(?:[-+# 0,()]*\d*(?:\.\d+)?)?[a-zA-Z%]|§[0-9a-frklmno]|https?://\S+|(?:minecraft|controlling):[a-z0-9_./-]+")
CACHE_LOCK=threading.Lock()
USER_AGENT="Mozilla/5.0 (compatible; ControllingLanguageExpansion-Marathi/1.0.1)"
OVERRIDES={
    "accessibility.onboarding.accessibility.button.narration":"प्रवेशयोग्यता सेटिंग्ज",
    "language.code":"mr_in",
}

def load(path:Path)->dict[str,str]:
    result=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result,dict) or not all(isinstance(k,str) and isinstance(v,str) for k,v in result.items()):
        raise ValueError(f"Invalid language JSON: {path}")
    return result

def save(path:Path,content:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(content,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")

def safe_tokens(reference:str,value:str)->bool:
    return sorted(TOKEN.findall(reference))==sorted(TOKEN.findall(value))

def translate_google(english:str)->str:
    query=urllib.parse.urlencode({"client":"gtx","sl":"en","tl":"mr","dt":"t","q":english})
    url="https://translate.googleapis.com/translate_a/single?"+query
    request=urllib.request.Request(url,headers={"User-Agent":USER_AGENT,"Accept":"application/json"})
    with urllib.request.urlopen(request,timeout=22) as f: payload=json.load(f)
    parts=payload[0]
    return unicodedata.normalize("NFC","".join(str(item[0]) for item in parts if item and item[0]))

def translate_with_retry(english:str)->tuple[str,str]:
    if not english.strip() or not re.search(r"[A-Za-z]",english):
        return english,"unchanged_literal"
    for attempt in range(4):
        try:
            out=translate_google(english)
            if out.strip() and safe_tokens(english,out):
                return out,"machine_google"
            if attempt==0 and TOKEN.search(english):
                # Retranslate only the unmasked segments; preserve technical literals exactly.
                sections=TOKEN.split(english)
                tokens=TOKEN.findall(english)
                rebuilt=[]
                for i,part in enumerate(sections):
                    if part:
                        t=translate_google(part)
                        rebuilt.append(t if t.strip() else part)
                    if i<len(tokens):rebuilt.append(tokens[i])
                candidate="".join(rebuilt)
                if safe_tokens(english,candidate):
                    return candidate,"machine_google_masked"
        except Exception:
            pass
        time.sleep([1.0,2.5,5.0,9.0][attempt])
    return english,"english_fallback_translation_unavailable"

def build(baseline:dict[str,str],target:dict[str,str],beyond:dict[str,str],
          cache_file:Path,max_workers:int)->tuple[dict[str,str],dict]:
    if len(baseline)!=7886 or len(beyond)!=7886 or set(baseline)!=set(beyond):
        raise ValueError("Expected matching official 26.1.2/Beyond & More 7886-key source")
    if len(target)!=8559 or not set(baseline)<=set(target):
        raise ValueError("Unexpected official Minecraft 26.3 English source or removed keys")
    previous_safe={k for k in baseline if k not in OVERRIDES and baseline[k]==target[k] and safe_tokens(target[k],beyond[k])}
    by_english=defaultdict(set)
    for k,value in baseline.items():
        if beyond[k]!=value and safe_tokens(value,beyond[k]):
            by_english[value].add(beyond[k])
    reusable={eng:next(iter(translations)) for eng,translations in by_english.items() if len(translations)==1}
    output={k:beyond[k] for k in previous_safe}
    from_bm_cross=[]
    pending={}
    sources={}
    for k in sorted(set(target)-previous_safe):
        english=target[k]
        if k in OVERRIDES:
            output[k]=OVERRIDES[k];sources[k]="curated"
        elif english in reusable and safe_tokens(english,reusable[english]):
            output[k]=reusable[english];from_bm_cross.append(k);sources[k]="beyond_same_english_other_key"
        else:
            pending[k]=english
    cached=json.loads(cache_file.read_text(encoding="utf-8")) if cache_file.exists() else {}
    unique=sorted(set(pending.values()))
    remaining=[s for s in unique if s not in cached or not cached[s].get("value") or cached[s]["method"]=="english_fallback_translation_unavailable"]
    print(f"Beyond & More same-key reuse: {len(previous_safe)}; same-English cross-key reuse: {len(from_bm_cross)}; curated: {len(OVERRIDES)}",flush=True)
    print(f"Untranslated source keys: {len(pending)}; unique strings: {len(unique)}; translation requests: {len(remaining)}",flush=True)
    def submit(phrase:str)->tuple[str,tuple[str,str]]:
        return phrase,translate_with_retry(phrase)
    n=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures={executor.submit(submit,english):english for english in remaining}
        for future in concurrent.futures.as_completed(futures):
            key=futures[future]
            try:phrase,(value,method)=future.result()
            except Exception as e:phrase=key;value=key;method=f"english_fallback_error_{type(e).__name__}"
            with CACHE_LOCK: cached[phrase]={"value":value,"method":method}
            n+=1
            if n%25==0 or n==len(remaining):
                save(cache_file,cached)
                print(f"Translated {n}/{len(remaining)} unique strings",flush=True)
    save(cache_file,cached)
    for k,english in pending.items():
        payload=cached.get(english,{"value":english,"method":"english_fallback_uncached"})
        translation=payload["value"]
        if not safe_tokens(english,translation):
            translation=english
            sources[k]="english_fallback_invalid_tokens"
        else:sources[k]=payload["method"]
        output[k]=translation
    if set(output)!=set(target) or any(not safe_tokens(target[k],output[k]) for k in target):
        raise ValueError("Incomplete output or corrupted technical placeholders")
    methods=defaultdict(int)
    for k in previous_safe:methods["beyond_same_key_same_english"]+=1
    for k in sources:methods[sources[k]]+=1
    report={
        "schema_version":1,"project_version":"1.0.1","minecraft":"26.3","locale":"mr_in",
        "name":"मराठी","region":"भारत","bidirectional":False,
        "source_beyond_and_more":"Beyond & More 26.1.2, assets/minecraft/lang/mr_in.json",
        "source_beyond_and_more_sha256":hashlib.sha256(DEFAULT_BM.read_bytes()).hexdigest(),
        "official_baseline":"26.1.2","official_target":"26.3",
        "official_baseline_english_keys":len(baseline),"official_target_english_keys":len(target),
        "added_keys":len(target.keys()-baseline.keys()),
        "changed_english_values":sum(baseline[k]!=target[k] for k in baseline),
        "translation_methods":dict(sorted(methods.items())),
        "remaining_english_values":sum(output[k]==target[k] for k in target),
        "machine_translation_requires_native_speaker_review":True,
        "notes":"Unchanged exact source values were taken directly from the user's Beyond & More Marathi translation. New and changed English source values were translated using Google Translate when available; cross-key inheritance is limited to uniquely identical English values."
    }
    return dict(sorted(output.items())),report

def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--baseline-en",type=Path,required=True)
    parser.add_argument("--target-en",type=Path,required=True)
    parser.add_argument("--beyond-marathi",type=Path,default=DEFAULT_BM)
    parser.add_argument("--cache",type=Path,default=ROOT/"translations/minecraft/26.3/machine_cache.json")
    parser.add_argument("--workers",type=int,default=5)
    args=parser.parse_args()
    baseline,target,beyond=(load(p) for p in (args.baseline_en,args.target_en,args.beyond_marathi))
    result,report=build(baseline,target,beyond,args.cache,args.workers)
    save(ROOT/"translations/minecraft/26.3/mr_in.json",result)
    save(ROOT/"translations/minecraft/26.3/provenance.json",report)
    print("PASS: generated 26.3 Minecraft Marathi pack source",report,flush=True)
    return 0

if __name__=="__main__":
    raise SystemExit(main())

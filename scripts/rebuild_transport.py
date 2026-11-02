#!/usr/bin/env python3
"""Lossless Zstandard transport with an explicit conditional curriculum block."""
import argparse,collections,concurrent.futures,ctypes,gzip,hashlib,json,random,re,time
from pathlib import Path
import tiktoken,zstandard
from grammar import conditional_sample,apply_grounding
from generate_corpus import clauses,tasks_for
from io_utils import write_bytes_atomic

SRC=DEST=None;REPLACEMENTS={};RECOVERED={};LEVEL=14
GEO=re.compile(r'[ა-ჰ]+')
def digest(s):return hashlib.blake2b(s,digest_size=12).digest()
def save_json(path,obj):write_bytes_atomic(path,(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())

def encoded_shard(path,raw,records):
    assert raw.endswith(b'\n') and raw.count(b'\n')==records
    encoded=zstandard.ZstdCompressor(level=LEVEL,write_checksum=True).compress(raw)
    recovered=zstandard.ZstdDecompressor().decompress(encoded)
    assert hashlib.sha256(recovered).digest()==hashlib.sha256(raw).digest()
    write_bytes_atomic(path,encoded)
    return {'path':path.relative_to(DEST).as_posix(),'records':records,'bytes':len(encoded),'sha256':hashlib.sha256(encoded).hexdigest(),'uncompressed_sha256':hashlib.sha256(raw).hexdigest(),'uncompressed_bytes':len(raw),'compression':'zstandard'}

def process_primary(spec):
    start,shard=spec;path=SRC/shard['path'];bad=RECOVERED.get(shard['path'])
    if bad:raw=Path(bad['prefix_path']).read_bytes();rows=[json.loads(x) for x in raw.splitlines()]
    else:
        raw=gzip.decompress(path.read_bytes());rows=None
    if rows is not None:
        assert len(rows)==bad['recovered_complete_records']
        for pos in range(len(rows),shard['records']):rows.append(REPLACEMENTS[start+pos])
        raw=b''.join(json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()+b'\n' for x in rows)
    elif any(start<=i<start+shard['records'] for i in REPLACEMENTS):
        rows=[json.loads(x) for x in raw.splitlines()]
        for pos in range(len(rows)):
            if start+pos in REPLACEMENTS:rows[pos]=REPLACEMENTS[start+pos]
        raw=b''.join(json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()+b'\n' for x in rows)
    stats=collections.Counter();kinds=collections.Counter();domains=collections.Counter();features=collections.Counter();families=collections.Counter()
    for pos,line in enumerate(raw.splitlines()):
        row=json.loads(line);assert row['id']==f'ka{start+pos:08}'
        stats['records']+=1;stats['tokens']+=row['lexical_tokens'];stats['full_tokens']+=row['text_tokens'];stats['words']+=len(GEO.findall(row['text_ka']));stats['units']+=len(clauses(row['text_ka']))
        kinds[row['construction']]+=1;domains[row['domain']]+=1;families[row['rule_family']]+=1
        for key,value in row['features'].items():features[key+'='+str(value)]+=1
    assert stats['records']==shard['records']
    target=DEST/shard['path'].replace('.jsonl.gz','.jsonl.zst');out=encoded_shard(target,raw,shard['records'])
    return out,stats,kinds,domains,features,families

def main():
    global SRC,DEST,REPLACEMENTS,RECOVERED,LEVEL
    p=argparse.ArgumentParser();p.add_argument('--input-root',type=Path,required=True);p.add_argument('--output-root',type=Path,required=True);p.add_argument('--integrity-report',type=Path)
    p.add_argument('--enrich-range');p.add_argument('--enrichment-seed',type=int,default=20261127);p.add_argument('--guard-library',type=Path,required=True);p.add_argument('--source-index',type=Path,required=True);p.add_argument('--workers',type=int,default=4);p.add_argument('--level',type=int,default=14)
    a=p.parse_args();SRC=a.input_root;DEST=a.output_root;LEVEL=a.level;DEST.mkdir(parents=True,exist_ok=True)
    assert not (DEST/'data/corpus').exists(),'Choose a clean transport output'
    manifest=json.loads((SRC/'data_manifest.json').read_text());report=json.loads((SRC/'generation_report.json').read_text())
    apply_grounding(json.loads((Path(__file__).resolve().parents[1]/'rules/lexical_grounding.json').read_text()))
    if a.integrity_report:
        scan=json.loads(a.integrity_report.read_text());RECOVERED={x['path']:x for x in scan['damaged'] if x['layer']=='corpus'}
        assert all(x['layer']=='corpus' for x in scan['damaged']),'Auxiliary repair requires regenerated tasks'
    specs=[];idx=1;missing=[]
    for shard in manifest['layers']['corpus']['shards']:
        specs.append((idx,shard))
        if shard['path'] in RECOVERED:
            b=RECOVERED[shard['path']];missing.extend(range(idx+b['recovered_complete_records'],idx+shard['records']))
        idx+=shard['records']
    if a.enrich_range:
        lo,hi=map(int,a.enrich_range.split(':'));missing=sorted(set(missing)|set(range(lo,hi+1)))
    lib=ctypes.CDLL(str(a.guard_library.resolve()));lib.load_index.argtypes=[ctypes.c_char_p];lib.contains_source_8gram.argtypes=[ctypes.c_char_p];assert lib.load_index(str(a.source_index.resolve()).encode())==1
    enc=tiktoken.get_encoding('o200k_base');r=random.Random(a.enrichment_seed);seen_core=set();seen_text=set();attempts=0
    for record_id in missing:
        while True:
            attempts+=1;row,core=conditional_sample(r);h=digest(json.dumps(core,ensure_ascii=False,separators=(',',':')).encode());parts=clauses(row['text_ka']);th=digest(' | '.join(parts).encode())
            if h in seen_core or th in seen_text or lib.contains_source_8gram(row['text_ka'].encode()):continue
            seen_core.add(h);seen_text.add(th)
            row={'id':f'ka{record_id:08}','synthetic_core_id':h.hex(),**row,'lexical_tokens':sum(len(enc.encode_ordinary(x)) for x in parts),'text_tokens':len(enc.encode_ordinary(row['text_ka']))}
            assert 'თუ' in GEO.findall(row['text_ka']);REPLACEMENTS[record_id]=row;break
    print(json.dumps({'conditional_records':len(REPLACEMENTS),'enrichment_attempts':attempts}),flush=True)
    stats=collections.Counter();kinds=collections.Counter();domains=collections.Counter();features=collections.Counter();families=collections.Counter();primary=[];start_time=time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers=a.workers) as pool:
        for i,result in enumerate(pool.map(process_primary,specs),1):
            out,st,ki,do,fe,fa=result;primary.append(out);stats.update(st);kinds.update(ki);domains.update(do);features.update(fe);families.update(fa)
            if i%10==0:print(json.dumps({'repacked_shards':i,'records':stats['records'],'tokens':stats['tokens'],'seconds':round(time.time()-start_time,1)}),flush=True)
    assert stats['tokens']>=150_000_000,'The completed primary payload must exceed 150 million tokens'
    new_manifest={'format':'UTF-8 JSONL; compression identified by file extension','layers':{'corpus':{'records':stats['records'],'shards':primary}}}
    q_replacements={}
    for i,row in REPLACEMENTS.items():
        if i%7==0:
            for offset,task in enumerate(tasks_for(row)):
                qid=f'qa{2*(i//7)-1+offset:08}';q_replacements[qid]={'id':qid,**task,'origin':'derived_from_synthetic'}
    for layer in ['role_tasks','case_corrections']:
        output=[];count=0
        for shard in manifest['layers'][layer]['shards']:
            lines=[]
            with gzip.open(SRC/shard['path'],'rt',encoding='utf-8') as f:
                for line in f:
                    row=json.loads(line);context_num=int(row['context_id'][2:])
                    if layer=='role_tasks':row=q_replacements.get(row['id'],row)
                    elif context_num in REPLACEMENTS:continue
                    count+=1
                    if layer=='case_corrections':row['id']=f'fix{count:07}'
                    lines.append(json.dumps(row,ensure_ascii=False,separators=(',',':')).encode()+b'\n')
            if lines:output.append(encoded_shard(DEST/shard['path'].replace('.jsonl.gz','.jsonl.zst'),b''.join(lines),len(lines)))
        new_manifest['layers'][layer]={'records':count,'shards':output}
    report.update(canonical_records=stats['records'],primary_georgian_lexical_tokens=stats['tokens'],full_primary_text_tokens=stats['full_tokens'],georgian_word_occurrences=stats['words'],unique_normalized_clauses=stats['units'],unique_lexical_cores=stats['records'],construction_counts=dict(kinds),domain_counts=dict(domains),feature_coverage=dict(features),rule_family_count=len(families),role_task_records=new_manifest['layers']['role_tasks']['records'],intentional_error_correction_records=new_manifest['layers']['case_corrections']['records'])
    report['conditional_curriculum_enrichment']={'records':len(REPLACEMENTS),'seed':a.enrichment_seed,'synthetic_record_ranges':[[min(missing),max(missing)]] if missing else [],'construction':'conditional','first_token_proves_separation_from_base_constructions':'თუ'}
    report['token_count_unit']='Token occurrences in Georgian words; every normalized sentence or dialogue utterance is counted once. Not distinct vocabulary types.'
    recipe={'base_generation_seed':report['seed'],'base_target_tokens':150000000,'conditional_enrichment_seed':a.enrichment_seed,'conditional_enrichment_record_ranges':report['conditional_curriculum_enrichment']['synthetic_record_ranges'],'compression':'zstandard','compression_level':LEVEL,'uncompressed_payload_hashes_verified':True}
    save_json(DEST/'generation_report.json',report);save_json(DEST/'data_manifest.json',new_manifest);save_json(DEST/'build_recipe.json',recipe)
    save_json(DEST/'transport_report.json',{'status':'PASS','primary_shards':len(primary),'all_repacked_payloads_roundtripped':True,'compression':'zstandard_with_checksum','data_bytes':sum(s['bytes'] for v in new_manifest['layers'].values() for s in v['shards']),'primary_records':stats['records'],'primary_georgian_lexical_tokens':stats['tokens']})
    print('COMPLETE '+json.dumps({'primary_tokens':stats['tokens'],'records':stats['records'],'data_bytes':sum(s['bytes'] for v in new_manifest['layers'].values()for s in v['shards'])}),flush=True)
if __name__=='__main__':main()

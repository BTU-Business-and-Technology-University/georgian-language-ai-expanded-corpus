#!/usr/bin/env python3
"""Validate auxiliary components separately from the primary token headline."""
import argparse,collections,gzip,hashlib,json,re,math
from pathlib import Path
from io_utils import open_text

if not __debug__:
    raise RuntimeError('Audit requires assertions enabled; run Python without -O or PYTHONOPTIMIZE')

FIELDS={
 'wordforms':{'id','form','char_length','document_frequency_band','clipped_occurrence_band','origin'},
 'adjacent_pairs':{'id','left','right','document_frequency_band','clipped_occurrence_band','origin'},
 'context_pairs':{'id','word_a','word_b','document_frequency_band','clipped_occurrence_band','dice_from_band_midpoints','origin'},
 'character_fragments':{'id','fragment','char_length','distinct_wordforms','clipped_occurrence_weight_band','origin'},
 'affix_statistics':{'id','position','fragment','char_length','distinct_wordforms','origin'}}
GEO=re.compile(r'[ა-ჰ]{2,30}\Z')

def run(root,manifest):
    total=orth=0;counts=collections.Counter();ids=set()
    for layer,spec in manifest['layers'].items():
        if not (layer.startswith('source_statistics/') or layer=='orthography_tasks'):continue
        n=0;feature_keys=set()
        for shard in spec['shards']:
            p=root/shard['path'];assert p.resolve().is_relative_to(root.resolve())
            assert p.stat().st_size==shard['bytes'] and p.stat().st_size<25*1024**2
            assert hashlib.sha256(p.read_bytes()).hexdigest()==shard['sha256']
            part=0
            payload_hash=hashlib.sha256()
            with open_text(p) as f:
                for line in f:
                    payload_hash.update(line.encode('utf-8'))
                    row=json.loads(line);part+=1;n+=1;assert row['id'] not in ids;ids.add(row['id'])
                    if layer.startswith('source_statistics/'):
                        subtype=layer.split('/')[-1];assert set(row)==FIELDS[subtype];assert row['origin']=='source_aggregate'
                        key_fields={'wordforms':('form',),'adjacent_pairs':('left','right'),'context_pairs':('word_a','word_b'),'character_fragments':('fragment',),'affix_statistics':('position','fragment')}[subtype]
                        key=tuple(row[k] for k in key_fields);assert key not in feature_keys;feature_keys.add(key)
                        for k in ['form','left','right','word_a','word_b','fragment']:
                            if k in row:assert GEO.fullmatch(row[k])
                        for k,v in row.items():
                            if k.endswith('_band'):assert isinstance(v,list) and len(v)==2 and all(type(x) is int for x in v) and v[0]>0 and v[1]==2*v[0]
                        if 'char_length' in row:assert row['char_length']==len(row.get('form',row.get('fragment')))
                        if 'distinct_wordforms' in row:assert type(row['distinct_wordforms']) is int and row['distinct_wordforms']>0
                        if subtype=='affix_statistics':assert row['position'] in {'prefix','suffix'}
                        if subtype=='context_pairs':
                            assert row['word_a']<row['word_b']
                            score=row['dice_from_band_midpoints'];assert type(score) in (float,int) and math.isfinite(score) and 0<=score<=1
                    else:
                        assert set(row)=={'id','task','wordform','question_ka','answer_ka','origin','spelling_gold','included_in_primary_token_headline'}
                        key=(row['task'],row['wordform']);assert key not in feature_keys;feature_keys.add(key)
                        w=row['wordform'];assert GEO.fullmatch(w);assert row['spelling_gold'] is False;assert row['included_in_primary_token_headline'] is False
                        assert row['origin']=='algorithmic_from_source_aggregate'
                        if row['task']=='letter_count':assert row['answer_ka']==str(len(w))
                        elif row['task']=='join_chunks':assert row['answer_ka']==w and row['question_ka'].endswith(' + '.join(w[i:i+2] for i in range(0,len(w),2)))
                        elif row['task']=='space_letters':assert row['answer_ka']==' '.join(w)
                        else:raise AssertionError(row['task'])
            assert part==shard['records']
            if 'uncompressed_sha256' in shard:assert payload_hash.hexdigest()==shard['uncompressed_sha256']
        assert n==spec['records'];counts[layer]=n
        if layer=='orthography_tasks':orth+=n
        else:total+=n
    return {'status':'PASS','source_aggregate_records_checked':total,'orthography_tasks_checked':orth,'component_counts':dict(counts),'format_or_field_errors':0,'orthographic_answer_errors':0,'duplicate_feature_or_exercise_keys':0,'included_in_primary_150m_token_headline':False,'gold_spelling_dictionary_claim':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--manifest',type=Path);p.add_argument('--report',type=Path);a=p.parse_args()
    manifest=json.loads((a.manifest or a.root/'data_manifest.json').read_text());r=run(a.root,manifest)
    if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(r,ensure_ascii=False))
if __name__=='__main__':main()

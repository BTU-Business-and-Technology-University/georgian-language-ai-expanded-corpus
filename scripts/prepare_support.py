#!/usr/bin/env python3
"""Preserve aggregate layers and add deterministic orthographic exercises."""
import argparse,collections,gzip,hashlib,json,random,re
from pathlib import Path
from generate_corpus import Shards,dump

BAD={'ფურცელები','ფურცელებს','ფანქარები','ფანქარებს','ჩანგალები','ჩანგალებს','ფიცარები','ფიცარებს','კალამები','კალამებს','მიზანები','მიზანებს','დერეფანები','დერეფანებს','ნაჭერები','ნაჭერებს'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--aggregate-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--name-filter',type=Path);a=p.parse_args()
    filters=json.loads(a.name_filter.read_text()) if a.name_filter else {'prefixes':[],'exact':[]}
    name_pattern=re.compile('^(?:'+'|'.join(re.escape(x)for x in filters['prefixes'])+')') if filters['prefixes'] else None
    exact=set(filters['exact']);suppressed=collections.Counter()
    source=json.loads((a.aggregate_root/'data_manifest.json').read_text());manifest={};selected=[]
    for layer,spec in source['layers'].items():
        writer=Shards(a.output,'source_statistics/'+layer,100000)
        for shard in spec['shards']:
            path=a.aggregate_root/shard['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==shard['sha256']
            with gzip.open(path,'rt',encoding='utf-8') as f:
                for line in f:
                    row=json.loads(line)
                    words=[row[k] for k in ['form','left','right','word_a','word_b','fragment'] if k in row]
                    if any(w in exact or (name_pattern and name_pattern.search(w)) for w in words):suppressed[layer]+=1;continue
                    writer.add({**row,'origin':'source_aggregate'})
                    if layer=='wordforms' and row['document_frequency_band'][0]>=64 and 4<=len(row['form'])<=24 and row['form'] not in BAD and not re.search(r'(.)\1\1',row['form']):selected.append(row['form'])
        manifest['source_statistics/'+layer]={**writer.finish(),'origin':'source_aggregate','training_use':'pooled statistical features; not continuous prose or gold spelling labels'}
    writer=Shards(a.output,'orthography_tasks',50000);r=random.Random(20261029)
    for word in selected:
        tasks=[('letter_count','რამდენი ასოა მოცემულ ფორმაში: '+word+'?',str(len(word))),
          ('join_chunks','შეაერთე ასოითი ნაწილები: '+' + '.join(word[i:i+2] for i in range(0,len(word),2)),word),
          ('space_letters','გამოყავი მოცემული ფორმის ასოები გამოტოვებებით: '+word,' '.join(word))]
        for task,q,answer in tasks:
            writer.add({'id':f'orth{writer.total+1:07}','task':task,'wordform':word,'question_ka':q,'answer_ka':answer,
                'origin':'algorithmic_from_source_aggregate','spelling_gold':False,'included_in_primary_token_headline':False})
    manifest['orthography_tasks']={**writer.finish(),'origin':'algorithmic_from_source_aggregate'}
    dump(a.output/'support_manifest.json',{'layers':manifest})
    dump(a.output/'support_report.json',{'source_aggregate_records':sum(v['records'] for k,v in manifest.items() if k.startswith('source_statistics/')),
      'orthographic_source_wordforms':len(selected),'orthography_task_records':writer.total,
      'known_nonstandard_plural_examples_excluded_from_orthographic_task_seeds':sorted(BAD),
      'orthographic_answers':'computed string transformations; no normative spelling or semantic-definition claim',
      'known_name_suppression_applied':a.name_filter is not None,'suppressed_records_by_layer':dict(suppressed),
      'name_filter_scope':'Known personal and literary name forms were suppressed; this is not a complete named-entity anonymization proof.',
      'included_in_primary_150m_token_count':False})
    print(json.dumps({'source_records':sum(v['records'] for k,v in manifest.items() if k.startswith('source_statistics/')),'orthography_tasks':writer.total,'selected_wordforms':len(selected)}),flush=True)
if __name__=='__main__':main()

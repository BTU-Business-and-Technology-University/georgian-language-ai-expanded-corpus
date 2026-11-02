import sys,json,hashlib
from pathlib import Path
r=Path(sys.argv[1]);sys.path.insert(0,str(r/'scripts'))
from io_utils import open_text
m=json.loads((r/'data_manifest.json').read_text());result={}
keys={'role_tasks':['context_id','task','question_ka','answer_ka'],'case_corrections':['context_id','task','incorrect_text_ka','correct_agent_ka'],'source_statistics/wordforms':['form'],'source_statistics/adjacent_pairs':['left','right'],'source_statistics/context_pairs':['word_a','word_b'],'source_statistics/character_fragments':['fragment'],'source_statistics/affix_statistics':['position','fragment'],'orthography_tasks':['task','wordform','question_ka','answer_ka']}
for name,fields in keys.items():
 seen=set();ids=set();duplicates=0;idduplicates=0;n=0;examples=[]
 for s in m['layers'][name]['shards']:
  with open_text(r/s['path']) as f:
   for line in f:
    row=json.loads(line);n+=1;key=tuple(row[k] for k in fields)
    if key in seen:
     duplicates+=1
     if len(examples)<10:examples.append(row['id'])
    seen.add(key);idduplicates+=row['id'] in ids;ids.add(row['id'])
 result[name]={'records':n,'identity_fields':fields,'duplicate_content_keys':duplicates,'duplicate_ids':idduplicates,'examples':examples}
 print(name,n,duplicates,idduplicates,flush=True)
(r/'reports/independent_2026_10_26/auxiliary_duplicates.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
assert all(v['duplicate_content_keys']==0 and v['duplicate_ids']==0 for v in result.values())

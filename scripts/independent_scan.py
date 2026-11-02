import sys,pathlib,json,gzip,subprocess,hashlib,collections,random,re,time
ROOT=pathlib.Path(sys.argv[1]).resolve()
sys.path.insert(0,str(ROOT/'scripts'))
from split_policy import target_group,group_split
from io_utils import open_text
if not __debug__: raise RuntimeError('Run independent scan without -O')
G=re.compile('[ა-ჰ]+'); rng=random.Random(2026102601)
out=pathlib.Path(sys.argv[2]);out.mkdir(exist_ok=True)
m=json.loads((ROOT/'data_manifest.json').read_text())
report={'seed':2026102601,'layers':{},'errors':[]};samples={}; seen=set();cores=set();vocab=collections.Counter(); signatures=collections.Counter();splits=collections.Counter();families=collections.Counter();domains=collections.Counter();contexts={};groups={};start=time.time()
def lines(p):
 with open_text(p) as stream: yield from stream
def sample(k,row):
 s=samples.setdefault(k,{'n':0,'rows':[]});s['n']+=1
 if len(s['rows'])<12:s['rows'].append(row)
 else:
  j=rng.randrange(s['n'])
  if j<12:s['rows'][j]=row
for name,spec in m['layers'].items():
 stats=collections.Counter(); types=collections.Counter(); fields=collections.Counter()
 for sh in spec['shards']:
  p=ROOT/sh['path'];raw=p.read_bytes()
  assert len(raw)==sh['bytes'] and hashlib.sha256(raw).hexdigest()==sh['sha256']
  h=hashlib.sha256();n=0
  for line in lines(p):
   n+=1;h.update(line.encode());r=json.loads(line);stats['records']+=1
   for k,v in r.items():fields[k]+=1;types[k+':'+type(v).__name__]+=1
   if name=='corpus':
    i=stats['records'];assert r['id']==f'ka{i:08d}'
    tx=r['text_ka'];w=G.findall(tx);stats['georgian_word_occurrences']+=len(w);vocab.update(w)
    stats['stored_lexical_tokens_sum']+=r['lexical_tokens'];stats['stored_text_tokens_sum']+=r['text_tokens']
    core=r['synthetic_core_id'];stats['duplicate_core_ids']+=core in cores;cores.add(core)
    for c in re.split('[.?!]+',tx):
     words=G.findall(c)
     if not words:continue
     dig=hashlib.sha256(' '.join(words).encode()).digest()[:16];stats['duplicate_normalized_clauses']+=dig in seen;seen.add(dig);stats['clauses']+=1
    group=target_group(r);sp=group_split(group);splits[sp]+=1;groups[group]=sp
    families[r['rule_family']]+=1;domains[r['domain']]+=1
    sig=(r['construction'],r['rule_family'].split(':')[1],group,r['features']['tense'],r['features']['polarity'])
    signatures[sig]+=1
    if any(x in tx for x in ['პირველი ','პირველ ','მეორე ','მესამე ']) and any(r['features'].get(k)=='plural' for k in ['patient_number','stimulus_number','possessed_number','subject_number']): stats['ordinal_plural_review']+=1
    for k,v in r['roles'].items():
     if v and v not in tx:stats['role_not_substring']+=1
    if i%7==0 or i%13==0:contexts[r['id']]=(sp,r['roles'],tx)
    sample('corpus/'+r['construction'],r)
   elif name in ['role_tasks','case_corrections']:
    c=contexts.get(r['context_id']);assert c is not None
    stats['split_'+c[0]]+=1
    if name=='role_tasks':
     assert r['answer_ka']==c[1][r['role']]
    else: assert r['correct_agent_ka']==c[1]['agent'] and r['include_in_plain_language_training'] is False
    sample(name,r)
   else:sample(name,r)
  assert n==sh['records'],(p,n,sh['records'])
  if 'uncompressed_sha256' in sh:assert h.hexdigest()==sh['uncompressed_sha256']
  if name=='corpus' and stats['records']%500000==0: print(name,stats['records'],round(time.time()-start),flush=True)
 assert stats['records']==spec['records']
 report['layers'][name]={'counts':dict(stats),'fields':dict(fields),'types':dict(types)}
 print('DONE',name,dict(stats),flush=True)
report.update(unique_normalized_clauses=len(seen),unique_wordforms=len(vocab),rule_families=len(families),domains=dict(domains),split_counts=dict(splits),target_groups=groups,semantic_signature_definition=['construction','predicate_or_subtype','target_head','tense','polarity'],semantic_signatures=len(signatures),largest_signature=max(signatures.values()),signature_top20=[{'key':list(k),'n':v} for k,v in signatures.most_common(20)],elapsed_seconds=time.time()-start)
(out/'scan.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
(out/'samples.json').write_text(json.dumps(samples,ensure_ascii=False,indent=2))
with (out/'samples.txt').open('w') as f:
 for k,s in samples.items():
  f.write('\n### '+k+' population '+str(s['n'])+'\n')
  for r in s['rows']: f.write(json.dumps(r,ensure_ascii=False)+'\n')
print('COMPLETE',flush=True)

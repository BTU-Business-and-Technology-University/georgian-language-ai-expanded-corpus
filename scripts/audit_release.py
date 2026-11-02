#!/usr/bin/env python3
"""Full streaming verification; token counts exclude annotations and metadata."""
import argparse,collections,ctypes,gzip,hashlib,json,random,re,time
from pathlib import Path
from lexicon import ACTORS,NOUNS,VERBS,adjective_options,object_phrase,storage_places
from grammar import PERSONAL,PRON_NOM,PRON_ERG,PRON_DAT,HAVE,MOTION,EXPERIENCERS
from io_utils import open_text
from generate_corpus import tasks_for
from split_policy import target_group,group_split,POLICY_VERSION

if not __debug__:
    raise RuntimeError('Audit requires assertions enabled; run Python without -O or PYTHONOPTIMIZE')

GEO=re.compile(r'[ა-ჰ]+');CLAUSE_SPLIT=re.compile(r'[.?!]+')
BAD_WORDS={'ფურცელები','ფურცელებს','ფანქარები','ფანქარებს','ჩანგალები','ჩანგალებს','ფიცარები','ფიცარებს','კალამები','კალამებს','მიზანები','მიზანებს','დერეფანები','დერეფანებს','ნაჭერები','ნაჭერებს'}
CASE_FIELDS={'nom':'nom','erg':'erg','dat':'dat'}
def normalized(s):return ' '.join(GEO.findall(s))
def hd(s):return hashlib.blake2b(s.encode(),digest_size=12).digest()
def task_digest(row):return hd(json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':')))
def stream(root,spec):
    total=0
    for shard in spec['shards']:
        p=root/shard['path'];assert p.resolve().is_relative_to(root.resolve()),p
        assert p.stat().st_size==shard['bytes'],p
        assert p.stat().st_size<25*1024**2,p
        assert hashlib.sha256(p.read_bytes()).hexdigest()==shard['sha256'],p
        n=0;payload_hash=hashlib.sha256()
        with open_text(p) as f:
            for line in f:n+=1;total+=1;payload_hash.update(line.encode('utf-8'));yield json.loads(line)
        assert n==shard['records'],p
        if 'uncompressed_sha256' in shard:assert payload_hash.hexdigest()==shard['uncompressed_sha256'],p
    assert total==spec['records'],('Manifest layer count mismatch',total,spec['records'])

def audit(root,guard_library=None,source_index=None,recount_tokens=True):
    start=time.time();m=json.loads((root/'data_manifest.json').read_text());summary=json.loads((root/'generation_report.json').read_text());enc=None
    if recount_tokens:
        import tiktoken
        enc=tiktoken.get_encoding('o200k_base')
    vmap={v.key:v for v in VERBS};actors={}
    for a in ACTORS:
        for pl in [False,True]:
            for case in ['nom','erg','dat']:
                form=(a.plural if case=='nom' else a.plural_erg if case=='erg' else a.plural_dat) if pl else getattr(a,case)
                actors[form]=(case,'plural' if pl else 'singular')
    noun_phrases=collections.defaultdict(list)
    for n in NOUNS:
        for a in adjective_options(n):
            for pl in [False,True]:
                if n.nom=='ტანსაცმელი' and pl:continue
                for case in ['nom','dat']:
                    noun_phrases[object_phrase(n,a,case,pl)].append((case,'plural' if pl else 'singular',n,a))
    def np(s,case,num=None):
        matches=[x for x in noun_phrases[s] if x[0]==case and (num is None or x[1]==num)]
        assert matches,('Invalid noun case or number',s,case,num);return matches[0]
    def actor(s,case,num):assert actors.get(s)==(case,num),('Invalid actor case/number',s,case,num)
    guard=None
    if guard_library is not None:
        assert source_index is not None
        guard=ctypes.CDLL(str(guard_library.resolve()));guard.load_index.argtypes=[ctypes.c_char_p];guard.contains_source_8gram.argtypes=[ctypes.c_char_p]
        assert guard.load_index(str(source_index.resolve()).encode())==1
    clauses_seen=set();cores_seen=set();records=token_total=full_token_total=words=0;counts=collections.Counter();families=set();expected_tasks=[];expected_corrections={};samples=collections.defaultdict(list);rnd=random.Random(20261028)
    split_counts=collections.Counter();split_tokens=collections.Counter();qa_splits=collections.Counter();fix_splits=collections.Counter();groups=collections.Counter();group_partitions={}
    domains=collections.Counter();feature_counts=collections.Counter();question_templates=set()
    nominatives={a.erg:a.nom for a in ACTORS};nominatives.update({a.plural_erg:a.plural for a in ACTORS})
    fields={'id','synthetic_core_id','text_ka','origin','construction','rule_family','domain','features','roles','lexical_tokens','text_tokens'}
    for row in stream(root,m['layers']['corpus']):
        records+=1;assert row['id']==f'ka{records:08}';assert set(row)==fields
        assert row['origin']=='rule_synthetic';assert row['synthetic_core_id'] not in cores_seen;cores_seen.add(row['synthetic_core_id'])
        text=row['text_ka'];assert text.endswith('.') and '  ' not in text
        assert all(('ა'<=c<='ჰ') or c in ' .,?!—\n' for c in text)
        tokens=GEO.findall(text);assert not BAD_WORDS.intersection(tokens)
        parts=[normalized(x) for x in CLAUSE_SPLIT.split(text) if GEO.search(x)]
        for part in parts:
            h=hd(part);assert h not in clauses_seen,('Repeated normalized clause',row['id']);clauses_seen.add(h)
        calculated=sum(len(enc.encode_ordinary(p)) for p in parts) if enc else row['lexical_tokens'];full=len(enc.encode_ordinary(text)) if enc else row['text_tokens']
        assert calculated==row['lexical_tokens'] and full==row['text_tokens']
        if guard is not None:assert guard.contains_source_8gram(text.encode())==0,('Source eight-word overlap',row['id'])
        token_total+=calculated;full_token_total+=full;words+=len(tokens);f=row['features'];roles=row['roles'];k=row['construction'];family=row['rule_family'].split(':')
        normalized_text=' '+normalized(text)+' '
        for role,value in roles.items():
            if value:assert ' '+normalized(value)+' ' in normalized_text,(row['id'],role,value)
        if k in {'active','relative'}:
            ti=['present','past','future'].index(f['tense']);expected_case='erg' if ti==1 else 'nom';object_case='nom' if ti==1 else 'dat'
            actor(roles['agent'],expected_case,f['agent_number']);np(roles['patient'],object_case,f['patient_number'])
            v=vmap[family[1]];assert roles['verb']==(v.plural if f['agent_number']=='plural' else v.singular)[ti]
        elif k=='conditional':
            actor(roles['agent'],'nom',f['agent_number']);np(roles['patient'],'dat',f['patient_number']);assert text.startswith('თუ ')
            v1,v2=vmap[family[1]],vmap[family[2]];sp=f['agent_number']=='plural'
            assert roles['verb']==(v1.plural if sp else v1.singular)[2]
            assert (v2.plural if sp else v2.singular)[2] in tokens
            assert ('ისინი' if sp else 'ის') in tokens
        elif k=='personal':
            ti=['present','past','future'].index(f['tense']);pi=f['person']-1+(3 if f['agent_number']=='plural' else 0)
            assert roles['agent']==(PRON_ERG if ti==1 else PRON_NOM)[pi]
            np(roles['patient'],'nom' if ti==1 else 'dat',f['patient_number']);assert roles['verb']==PERSONAL[family[1]][ti][pi]
        elif k=='modal':
            actor(roles['agent'],'dat' if f['modality']=='ability' else 'erg',f['agent_number']);np(roles['patient'],'nom',f['patient_number'])
            v=vmap[family[1]];assert roles['verb']==(v.opt_pl if f['agent_number']=='plural' else v.opt_sg)
            modal=('შეუძლიათ' if f['agent_number']=='plural' else 'შეუძლია') if f['modality']=='ability' else 'უნდა';assert modal in tokens
        elif k=='passive':
            ti=['present','past_imperfect','future'].index(f['tense']);assert f['verb_number']=='singular'
            np(roles['patient'],'nom',f['patient_number']);assert roles['agent'] in {a.gen+' მიერ' for a in ACTORS}
            assert roles['verb']==vmap[family[1]].passive[ti]
        elif k=='temporal':
            actor(roles['agent'],'erg',f['agent_number']);np(roles['patient'],'nom',f['patient_number']);assert len(parts)==2
            v=vmap[family[1]];forms=v.plural if f['agent_number']=='plural' else v.singular
            assert forms[1] in GEO.findall(text.split('.')[0]);assert forms[2] in GEO.findall(text.split('.')[1])
            assert ('ისინი' if f['agent_number']=='plural' else 'ის') in GEO.findall(text.split('.')[1])
        elif k=='experiencer':
            actor(roles['experiencer'],'dat',f['experiencer_number']);np(roles['stimulus'],'nom',f['stimulus_number'])
            ex={key:(sg,pl) for key,sg,pl in EXPERIENCERS}[family[1]];ti=['present','past_imperfect','future'].index(f['tense']);assert roles['verb']==ex[f['experiencer_number']=='plural'][ti]
        elif k=='possession':
            ti=['present','past','future'].index(f['tense']);np(roles['possessed'],'nom',f['possessed_number'])
            if roles['possessor'] in PRON_DAT:
                pi=f['person']-1+(3 if f['possessor_number']=='plural' else 0);assert roles['possessor']==PRON_DAT[pi]
            else:actor(roles['possessor'],'dat',f['possessor_number']);pi=5 if f['possessor_number']=='plural' else 2
            assert roles['verb']==HAVE[ti][pi]
            _,_,n,ad=np(roles['possessed'],'nom',f['possessed_number']);assert roles['place'] in storage_places(n,ad)
        elif k=='motion':
            actor(roles['mover'],'nom',f['subject_number']);mv={key:(sg,pl) for key,sg,pl in MOTION}[family[1]];ti=['present','past','future'].index(f['tense']);assert roles['verb']==mv[f['subject_number']=='plural'][ti]
        elif k in {'genitive','dialogue'}:
            assert roles['possessor'] in {a.gen for a in ACTORS}
            assert roles['located'].startswith(roles['possessor']+' ')
            phrase=roles['located'][len(roles['possessor'])+1:];_,_,n,ad=np(phrase,'nom',f['subject_number'])
            assert roles['place'] in storage_places(n,ad);assert roles['verb']==['არის','იყო','იქნება'][['present','past','future'].index(f['tense'])]
            assert f['verb_number']=='singular';assert len(parts)==(2 if k=='dialogue' else 1)
        else:raise AssertionError(k)
        if f['polarity']=='negative':assert 'არ' in tokens
        counts[k]+=1;families.add(row['rule_family'])
        group=target_group(row);split=group_split(group);groups[group]+=1
        assert group not in group_partitions or group_partitions[group]==split
        group_partitions[group]=split;split_counts[split]+=1;split_tokens[split]+=calculated
        domains[row['domain']]+=1
        for feature,value in f.items():feature_counts[feature+'='+str(value)]+=1
        if records%7==0:
            for task in tasks_for(row):
                expected_tasks.append(task_digest(task));qa_splits[split]+=1;question_templates.add(task['question_ka'])
        if records%13==0 and k=='active' and f['tense']=='past':
            expected_corrections[row['id']]=(text,roles['agent'],nominatives[roles['agent']]);fix_splits[split]+=1
        if len(samples[k])<20:samples[k].append(row)
        elif rnd.randrange(counts[k])<20:samples[k][rnd.randrange(20)]=row
        if records%100000==0:print(json.dumps({'audited_records':records,'lexical_tokens':token_total,'seconds':round(time.time()-start,1)}),flush=True)
    assert records==summary['canonical_records'];assert token_total==summary['primary_georgian_lexical_tokens'];assert token_total>=summary['target_primary_georgian_lexical_tokens']
    assert full_token_total==summary['full_primary_text_tokens'];assert words==summary['georgian_word_occurrences'];assert dict(counts)==summary['construction_counts']
    if 'domain_counts' in summary:assert dict(domains)==summary['domain_counts']
    if 'feature_coverage' in summary:assert dict(feature_counts)==summary['feature_coverage']
    if 'rule_family_count' in summary:assert len(families)==summary['rule_family_count']
    qa_count=0
    for row in stream(root,m['layers']['role_tasks']):
        qa_count+=1;assert row['id']==f'qa{qa_count:08}' and row['origin']=='derived_from_synthetic'
        assert set(row)=={'id','context_id','task','role','question_ka','answer_ka','origin'}
        assert task_digest({key:value for key,value in row.items() if key not in {'id','origin'}})==expected_tasks[qa_count-1],('Task differs from positive context or current question policy',row['id'])
        assert row['question_ka'].endswith(('?','.'))
    assert qa_count==summary['role_task_records']
    fix_count=0
    for row in stream(root,m['layers']['case_corrections']):
        fix_count+=1;assert row['id']==f'fix{fix_count:07}' and row['include_in_plain_language_training'] is False
        assert set(row)=={'id','context_id','task','question_ka','incorrect_text_ka','correct_agent_ka','origin','include_in_plain_language_training'}
        assert row['origin']=='deliberate_negative_from_synthetic' and row['task']=='correct_agent_case'
        assert row['question_ka']=='გაასწორე მოქმედი პირის ბრუნვა.'
        good,agent,wrong=expected_corrections[row['context_id']];assert row['correct_agent_ka']==agent
        assert row['incorrect_text_ka']==good.replace(agent,wrong,1),('Unexpected correction mutation',row['id'])
        assert row['incorrect_text_ka']!=good and len(GEO.findall(row['incorrect_text_ka']))==len(GEO.findall(good))
    assert fix_count==summary['intentional_error_correction_records']
    result={'status':'PASS' if recount_tokens else 'PASS_STRUCTURAL_TOKEN_RECOUNT_SKIPPED','token_counts_independently_recomputed':recount_tokens,'primary_records_checked':records,'primary_georgian_lexical_tokens':token_total,'primary_full_text_tokens':full_token_total,'unique_normalized_clauses_checked':len(clauses_seen),
      'unique_lexical_core_ids_checked':len(cores_seen),'rule_families_checked':len(families),'construction_counts':dict(counts),'role_tasks_checked':qa_count,'intentional_negative_examples_checked':fix_count,
      'exact_clause_duplicates':0,'invalid_paradigm_or_case_assignments':0,'incorrect_known_irregular_plurals':0,'unexpected_primary_data_fields':0,'token_count_mismatches':0 if recount_tokens else None,
      'source_8gram_full_rescan_completed':guard is not None,'source_8gram_matches_in_accepted_primary_texts':0 if guard is not None else None,
      'question_policy':'neutral_span_extraction_v2.0.1','question_templates_checked':len(question_templates),'all_task_payloads_match_linked_positive_contexts':True,
      'split_policy':POLICY_VERSION,'split_primary_records':dict(split_counts),'split_primary_lexical_tokens':dict(split_tokens),'split_role_tasks':dict(qa_splits),'split_case_corrections':dict(fix_splits),
      'target_groups':{g:{'split':group_partitions[g],'primary_records':groups[g]} for g in sorted(groups)},'target_groups_shared_between_splits':0,
      'formal_non_reidentification_proof':False,'independent_human_linguist_review':False,'trained_model_quality_gain_verified':False,'elapsed_seconds':round(time.time()-start,2)}
    return result,samples

def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--guard-library',type=Path);p.add_argument('--source-index',type=Path);p.add_argument('--report',type=Path);p.add_argument('--samples',type=Path)
    p.add_argument('--skip-token-recount',action='store_true',help='Structural checks only; token totals are unverified stored sums')
    a=p.parse_args();result,samples=audit(a.root,a.guard_library,a.source_index,not a.skip_token_recount)
    if a.report:a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    if a.samples:a.samples.write_text(json.dumps(samples,ensure_ascii=False,indent=2)+'\n')
    print('COMPLETE '+json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':main()

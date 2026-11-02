#!/usr/bin/env python3
"""Build unique, source-screened synthetic Georgian language examples."""
import argparse,collections,ctypes,gzip,hashlib,io,json,os,random,re,time
from pathlib import Path
from grammar import KINDS,sample,assert_constructed,ACTORS,apply_grounding
from io_utils import write_bytes_atomic

GEO=re.compile(r'[ა-ჰ]+')
def digest(value):return hashlib.blake2b(value,digest_size=12).digest()
def dump(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix(path.suffix+'.part')
    with tmp.open('w',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)

class Shards:
    def __init__(self,root,layer,limit=25000):
        self.root=root;self.layer=layer;self.limit=limit;self.part=0;self.rows=0;self.total=0;self.writer=None;self.entries=[]
    def close(self):
        if self.writer is None:return
        self.writer.close();data=self.binary.getvalue();self.binary.close()
        assert gzip.decompress(data).count(b'\n')==self.rows
        write_bytes_atomic(self.path,data)
        self.entries.append({'path':self.path.relative_to(self.root).as_posix(),'records':self.rows,'bytes':self.path.stat().st_size,'sha256':hashlib.sha256(self.path.read_bytes()).hexdigest()})
        self.writer=None
    def add(self,obj):
        if self.writer is None or self.rows>=self.limit:
            self.close();self.rows=0;self.part+=1;self.path=self.root/'data'/self.layer/f'part-{self.part:05}.jsonl.gz';self.path.parent.mkdir(parents=True,exist_ok=True)
            self.binary=io.BytesIO()
            self.writer=io.TextIOWrapper(gzip.GzipFile(filename=self.path.name,fileobj=self.binary,mode='wb',compresslevel=5,mtime=0),encoding='utf-8')
        self.writer.write(json.dumps(obj,ensure_ascii=False,separators=(',',':'))+'\n');self.rows+=1;self.total+=1
    def finish(self):self.close();return {'records':self.total,'shards':self.entries}

def clauses(text):
    return [' '.join(GEO.findall(x)) for x in re.split(r'[.?!]+',text) if GEO.search(x)]

def tasks_for(row):
    roles=row['roles'];result=[]
    questions={'agent':'ამოიღე ტექსტიდან მოქმედი პირის აღმნიშვნელი ფორმა.','patient':'ამოიღე ტექსტიდან მოქმედების ობიექტის აღმნიშვნელი ფორმა.','time':'ამოიღე ტექსტიდან დროის აღმნიშვნელი გამოთქმა.','place':'ამოიღე ტექსტიდან ადგილის აღმნიშვნელი გამოთქმა.','experiencer':'რომელ პირს ეხება წინადადება? ამოიღე ტექსტში გამოყენებული ფორმა.','stimulus':'რომელ საგანს ან საკითხს ეხება განცდა ან საჭიროება? ამოიღე შესაბამისი ფორმა.','possessor':'რომელ პირზეა საუბარი? ამოიღე ტექსტში გამოყენებული ფორმა.','possessed':'რომელ საგანზეა საუბარი? ამოიღე ტექსტში გამოყენებული ფორმა.','mover':'ვის გადაადგილებას ან დარჩენას ეხება ტექსტი? ამოიღე შესაბამისი ფორმა.','destination':'ამოიღე ტექსტიდან დანიშნულების ან დარჩენის ადგილი.'}
    for role in ['agent','patient'] if row['construction'] in {'active','relative','personal','modal','conditional'} else ['possessor','possessed'] if row['construction']=='possession' else ['experiencer','stimulus'] if row['construction']=='experiencer' else ['mover','destination'] if row['construction']=='motion' else ['time','place']:
        question=questions[role]
        if row['construction']=='temporal' and role=='time':question='ამოიღე პირველი წინადადებიდან დროის აღმნიშვნელი გამოთქმა.'
        if row['construction']=='temporal' and role=='place':question='ამოიღე პირველი წინადადებიდან ადგილის აღმნიშვნელი გამოთქმა.'
        if roles.get(role):result.append({'context_id':row['id'],'task':'extract_role','role':role,'question_ka':question,'answer_ka':roles[role]})
    return result

def main():
    import tiktoken
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--work-dir',type=Path,required=True)
    p.add_argument('--guard-library',type=Path,required=True);p.add_argument('--source-index',type=Path,required=True)
    p.add_argument('--target-tokens',type=int,default=150_000_000);p.add_argument('--seed',type=int,default=20261026)
    a=p.parse_args();a.root.mkdir(parents=True,exist_ok=True);a.work_dir.mkdir(parents=True,exist_ok=True)
    assert not (a.root/'data/corpus').exists(),'Use a clean output root to avoid stale shards'
    grounding=Path(__file__).resolve().parents[1]/'rules/lexical_grounding.json'
    apply_grounding(json.loads(grounding.read_text()))
    lib=ctypes.CDLL(str(a.guard_library.resolve()));lib.load_index.argtypes=[ctypes.c_char_p];lib.contains_source_8gram.argtypes=[ctypes.c_char_p]
    assert lib.load_index(str(a.source_index.resolve()).encode())==1
    enc=tiktoken.get_encoding('o200k_base');r=random.Random(a.seed)
    corpus=Shards(a.root,'corpus');qa=Shards(a.root,'role_tasks');correction=Shards(a.root,'case_corrections')
    seen_cores=set();seen_texts=set();seen_clauses=set();c=collections.Counter();counts=collections.Counter();domains=collections.Counter();families=collections.Counter();features=collections.Counter()
    tokens=full_tokens=word_count=0;start=time.time();review_samples=collections.defaultdict(list);actor_nom={x.erg:x.nom for x in ACTORS};actor_nom.update({x.plural_erg:x.plural for x in ACTORS})
    while tokens<a.target_tokens:
        if c['attempts']%1000==0 and (a.work_dir/'CANCEL').exists():raise RuntimeError('Cancelled for review through private work marker')
        c['attempts']+=1;kind=KINDS[(c['attempts']-1)%len(KINDS)]
        row,core,slots=sample(r,kind)
        corehash=digest(json.dumps(core,ensure_ascii=False,separators=(',',':')).encode())
        if corehash in seen_cores:c['rejected_repeated_lexical_core']+=1;continue
        text=row['text_ka'];parts=clauses(text);ph=[digest(s.encode()) for s in parts]
        if len(set(ph))!=len(ph) or any(h in seen_clauses for h in ph):c['rejected_repeated_clause']+=1;continue
        th=digest(' | '.join(parts).encode())
        if th in seen_texts:c['rejected_repeated_text']+=1;continue
        if not 5<=sum(s.count(' ')+1 for s in parts)<=65:c['rejected_length']+=1;continue
        assert_constructed(row)
        match=lib.contains_source_8gram(text.encode())
        if match<0:raise RuntimeError('Source guard unavailable')
        if match:c['rejected_source_overlap_or_bloom_positive']+=1;continue
        count=sum(len(enc.encode_ordinary(s)) for s in parts);full=len(enc.encode_ordinary(text))
        seen_cores.add(corehash);seen_texts.add(th);seen_clauses.update(ph)
        tokens+=count;full_tokens+=full;word_count+=sum(s.count(' ')+1 for s in parts)
        idx=corpus.total+1;row={'id':f'ka{idx:08}','synthetic_core_id':corehash.hex(),**row,'lexical_tokens':count,'text_tokens':full}
        corpus.add(row);counts[kind]+=1;domains[row['domain']]+=1;families[row['rule_family']]+=1
        for key,value in row['features'].items():features[key+'='+str(value)]+=1
        if len(review_samples[kind])<25:review_samples[kind].append(row)
        if idx%7==0:
            for task in tasks_for(row):qa.add({'id':f'qa{qa.total+1:08}',**task,'origin':'derived_from_synthetic'})
        if idx%13==0 and kind=='active' and row['features']['tense']=='past':
            wrong_nom=actor_nom.get(row['roles']['agent'])
            if wrong_nom:
                bad=text.replace(row['roles']['agent'],wrong_nom,1)
                correction.add({'id':f'fix{correction.total+1:07}','context_id':row['id'],'task':'correct_agent_case','question_ka':'გაასწორე მოქმედი პირის ბრუნვა.','incorrect_text_ka':bad,'correct_agent_ka':row['roles']['agent'],'origin':'deliberate_negative_from_synthetic','include_in_plain_language_training':False})
        if idx%25000==0:
            state={'records':idx,'primary_georgian_lexical_tokens':tokens,'full_text_tokens':full_tokens,'unique_clauses':len(seen_clauses),'attempts':c['attempts'],'elapsed_seconds':round(time.time()-start,1),'construction_counts':dict(counts),'rejections':dict(c)}
            dump(a.work_dir/'generation_progress.json',state);print(json.dumps(state,ensure_ascii=False),flush=True)
    manifest={'format':'UTF-8 JSONL gzip','layers':{'corpus':corpus.finish(),'role_tasks':qa.finish(),'case_corrections':correction.finish()}}
    report={'version':'2.0.1','origin':'rule_based_synthetic_with_aggregate_lexical_support','encoding':'o200k_base','target_primary_georgian_lexical_tokens':a.target_tokens,
      'canonical_records':corpus.total,'primary_georgian_lexical_tokens':tokens,'full_primary_text_tokens':full_tokens,'georgian_word_occurrences':word_count,
      'unique_normalized_clauses':len(seen_clauses),'unique_lexical_cores':len(seen_cores),'construction_counts':dict(counts),'domain_counts':dict(domains),'rule_family_count':len(families),'feature_coverage':dict(features),
      'role_task_records':qa.total,'intentional_error_correction_records':correction.total,'counted_token_fields':['corpus.text_ka Georgian words only, each normalized clause once'],
      'excluded_from_headline_token_count':['IDs','JSON syntax','metadata','roles repeated from text','task prompts','task answers','negative examples','documentation','lexical support statistics'],
      'exact_normalized_text_duplicates':0,'exact_normalized_clause_duplicates':0,'max_examples_per_lexical_core':1,'all_candidates_source_8gram_screened':True,
      'source_guard_kind':'conservative Bloom membership filter over processed private corpus normalized contiguous eight-word windows','accepted_source_8gram_matches':0,
      'universal_source_nonidentifiability_proven':False,'independent_human_linguist_review_completed':False,'model_utility_evaluation_completed':False,
      'seed':a.seed,'elapsed_seconds':round(time.time()-start,2),'rejections':dict(c)}
    dump(a.root/'data_manifest.json',manifest);dump(a.root/'generation_report.json',report);dump(a.work_dir/'review_samples.json',dict(review_samples));dump(a.work_dir/'rule_family_counts.json',dict(families))
    print('COMPLETE '+json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':main()

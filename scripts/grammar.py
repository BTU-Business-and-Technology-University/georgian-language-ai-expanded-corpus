"""Controlled Georgian construction families; generated, not gold annotations."""
import random
from dataclasses import replace
from lexicon import *

TENSES=['present','past','future']
KINDS=['active','active','active','relative','temporal','modal','passive','experiencer','possession','motion','dialogue','genitive','personal','personal']
VERB_BY_KEY={v.key:v for v in VERBS}
PASSIVES=[v for v in VERBS if v.passive]
def apply_grounding(data):
    allowed=data['allowed_predicate_noun_pairs'];selected=[]
    for v in VERBS:
        names={x['noun'] for x in allowed.get(v.key,[])}
        objects=tuple(dict.fromkeys(n for n in v.objects if n.nom in names))
        if objects:selected.append(replace(v,objects=objects))
    VERBS[:]=selected;VERB_BY_KEY.clear();VERB_BY_KEY.update({v.key:v for v in VERBS});PASSIVES[:]=[v for v in VERBS if v.passive]
    assert len(VERBS)>=30,'Insufficient grounded verb coverage'
PERSONAL={
 'write':[
  'ვწერ/წერ/წერს/ვწერთ/წერთ/წერენ',
  'დავწერე/დაწერე/დაწერა/დავწერეთ/დაწერეთ/დაწერეს',
  'დავწერ/დაწერ/დაწერს/დავწერთ/დაწერთ/დაწერენ'],
 'read':[
  'ვკითხულობ/კითხულობ/კითხულობს/ვკითხულობთ/კითხულობთ/კითხულობენ',
  'წავიკითხე/წაიკითხე/წაიკითხა/წავიკითხეთ/წაიკითხეთ/წაიკითხეს',
  'წავიკითხავ/წაიკითხავ/წაიკითხავს/წავიკითხავთ/წაიკითხავთ/წაიკითხავენ'],
 'prepare':[
  'ვამზადებ/ამზადებ/ამზადებს/ვამზადებთ/ამზადებთ/ამზადებენ',
  'მოვამზადე/მოამზადე/მოამზადა/მოვამზადეთ/მოამზადეთ/მოამზადეს',
  'მოვამზადებ/მოამზადებ/მოამზადებს/მოვამზადებთ/მოამზადებთ/მოამზადებენ'],
 'check':[
  'ვამოწმებ/ამოწმებ/ამოწმებს/ვამოწმებთ/ამოწმებთ/ამოწმებენ',
  'შევამოწმე/შეამოწმე/შეამოწმა/შევამოწმეთ/შეამოწმეთ/შეამოწმეს',
  'შევამოწმებ/შეამოწმებ/შეამოწმებს/შევამოწმებთ/შეამოწმებთ/შეამოწმებენ'],
 'understand':[
  'ვიგებ/იგებ/იგებს/ვიგებთ/იგებთ/იგებენ',
  'გავიგე/გაიგე/გაიგო/გავიგეთ/გაიგეთ/გაიგეს',
  'გავიგებ/გაიგებ/გაიგებს/გავიგებთ/გაიგებთ/გაიგებენ'],
 'learn':[
  'ვსწავლობ/სწავლობ/სწავლობს/ვსწავლობთ/სწავლობთ/სწავლობენ',
  'ვისწავლე/ისწავლე/ისწავლა/ვისწავლეთ/ისწავლეთ/ისწავლეს',
  'ვისწავლი/ისწავლი/ისწავლის/ვისწავლით/ისწავლით/ისწავლიან'],
 'create':[
  'ვქმნი/ქმნი/ქმნის/ვქმნით/ქმნით/ქმნიან',
  'შევქმენი/შექმენი/შექმნა/შევქმენით/შექმენით/შექმნეს',
  'შევქმნი/შექმნი/შექმნის/შევქმნით/შექმნით/შექმნიან'],
 'explain':[
  'ვხსნი/ხსნი/ხსნის/ვხსნით/ხსნით/ხსნიან',
  'ავხსენი/ახსენი/ახსნა/ავხსენით/ახსენით/ახსნეს',
  'ავხსნი/ახსნი/ახსნის/ავხსნით/ახსნით/ახსნიან'],
 'choose':[
  'ვირჩევ/ირჩევ/ირჩევს/ვირჩევთ/ირჩევთ/ირჩევენ',
  'ავირჩიე/აირჩიე/აირჩია/ავირჩიეთ/აირჩიეთ/აირჩიეს',
  'ავირჩევ/აირჩევ/აირჩევს/ავირჩევთ/აირჩევთ/აირჩევენ'],
 'change':[
  'ვცვლი/ცვლი/ცვლის/ვცვლით/ცვლით/ცვლიან',
  'შევცვალე/შეცვალე/შეცვალა/შევცვალეთ/შეცვალეთ/შეცვალეს',
  'შევცვლი/შეცვლი/შეცვლის/შევცვლით/შეცვლით/შეცვლიან']}
PERSONAL={k:tuple(tuple(x.split('/')) for x in forms) for k,forms in PERSONAL.items()}
PRON_NOM=['მე','შენ','ის','ჩვენ','თქვენ','ისინი']
PRON_ERG=['მე','შენ','მან','ჩვენ','თქვენ','მათ']
PRON_DAT=['მე','შენ','მას','ჩვენ','თქვენ','მათ']
HAVE=[
 ['მაქვს','გაქვს','აქვს','გვაქვს','გაქვთ','აქვთ'],
 ['მქონდა','გქონდა','ჰქონდა','გვქონდა','გქონდათ','ჰქონდათ'],
 ['მექნება','გექნება','ექნება','გვექნება','გექნებათ','ექნებათ']]

def surface(parts):return ' '.join(x for x in parts if x).strip()+'.'
def aform(a,case,pl):return actor_form(a,case,pl)
def object_selection(r,v=None):
    n=r.choice(v.objects if v else NOUNS);adj=r.choice(adjective_options(n));pl=r.random()<.35
    if n.nom in {'ტანსაცმელი'}:pl=False
    if v and v.key in {'count','combine'}:pl=True
    if v and v.key in {'sort','collect'} and n.nom!='მასალა':pl=True
    if v and v.key=='correct' and adj[0]=='შესწორებული':adj=('ახალი','ახალ')
    if v and v.key=='update' and adj[0]=='განახლებული':adj=('ახალი','ახალ')
    return n,adj,pl

def assemble_clause(time,actor,patient,place,manner,verb,negative,order):
    vp=('არ ' if negative else '')+verb
    if order==0:return surface([time,place,actor,patient,manner,vp])
    if order==1:return surface([actor,time,place,patient,manner,vp])
    if order==2:return surface([actor,patient,time,place,manner,vp])
    return surface([time,actor,patient,manner,vp,place])

def sample(r,kind):
    a=r.choice(ACTORS);aidx=ACTORS.index(a);sp=r.random()<.4;ti=r.randrange(3);tense=TENSES[ti]
    negative=r.random()<.2;time=r.choice(TIMES[tense]);order=r.randrange(4)
    v=r.choice(VERBS);n,adj,op=object_selection(r,v)
    a=r.choice(suitable_actors(v,n));aidx=ACTORS.index(a)
    place=r.choice(action_places(v,n));manner='' if negative else r.choice(manner_options(v))
    acase='erg' if ti==1 else 'nom';ocase='nom' if ti==1 else 'dat'
    agent=aform(a,acase,sp);patient=object_phrase(n,adj,ocase,op);vb=(v.plural if sp else v.singular)[ti]
    roles={'agent':agent,'patient':patient,'time':time,'place':place,'manner':manner,'verb':vb}
    features={'tense':tense,'agent_number':'plural' if sp else 'singular','patient_number':'plural' if op else 'singular','agent_case':acase,'patient_case':ocase,'polarity':'negative' if negative else 'positive'}
    core=[kind,v.key,aidx,sp,n.nom,adj,op,ti,negative]
    slots=[time,place,manner]
    family=[kind,v.key,tense,features['agent_number'],features['patient_number'],features['polarity'],str(order)]

    if kind=='active':
        text=assemble_clause(time,agent,patient,place,manner,vb,negative,order)
    elif kind=='relative':
        relplace=r.choice(PLACES[n.domain]);relverb='მუშაობენ' if sp else 'მუშაობს';relpron='რომლებიც' if sp else 'რომელიც'
        expanded=agent+', '+relpron+' '+relplace+' '+relverb+','
        text=assemble_clause(time,expanded,patient,place,manner,vb,negative,order)
        slots.append(relplace);features['relative_clause']='nominative_relative_subject'
    elif kind=='temporal':
        v=r.choice([x for x in VERBS if x.key in {'read','check','correct','prepare','translate','print','write','study','evaluate'}])
        n,adj,op=object_selection(r,v);place=r.choice(action_places(v,n));manner=r.choice(manner_options(v))
        a=r.choice(suitable_actors(v,n));aidx=ACTORS.index(a)
        time=r.choice(TIMES['past']);next_time=r.choice(TIMES['future'])
        agent=aform(a,'erg',sp);patient=object_phrase(n,adj,'nom',op)
        pron='ისინი' if sp else 'ის';ref='ამ '+(n.plural_dat if op else n.dat)
        first=assemble_clause(time,agent,patient,place,manner,(v.plural if sp else v.singular)[1],False,order)
        second=surface([next_time,pron,place,ref,'კიდევ ერთხელ',manner,(v.plural if sp else v.singular)[2]])
        text=first+' '+second
        roles={'agent':agent,'patient':patient,'time':time,'place':place,'manner':manner,'verb':(v.plural if sp else v.singular)[1]}
        features.update(tense='past_then_future',agent_case='erg',patient_case='nom',patient_number='plural' if op else 'singular',polarity='positive',coreference='human_pronoun_and_demonstrative_object')
        core=[kind,v.key,aidx,sp,n.nom,adj,op];slots=[time,next_time,place,manner]
        family=[kind,v.key,features['agent_number'],features['patient_number'],str(order)]
    elif kind=='modal':
        ti=0;time=r.choice(TIMES['present']);ability=r.random()<.5
        acase='dat' if ability else 'erg';agent=aform(a,acase,sp);patient=object_phrase(n,adj,'nom',op)
        modal=('შეუძლიათ' if sp else 'შეუძლია') if ability else 'უნდა'
        modal=('არ ' if negative else '')+modal;subverb=v.opt_pl if sp else v.opt_sg
        text=surface([time,place,agent,modal,patient,manner,subverb] if ability else [time,place,agent,patient,manner,modal,subverb])
        roles={'agent':agent,'patient':patient,'time':time,'place':place,'manner':manner,'verb':subverb}
        features.update(tense='present_modal',agent_case=acase,patient_case='nom',modality='ability' if ability else 'obligation')
        core=[kind,v.key,aidx,sp,n.nom,adj,op,ability,negative];slots=[time,place,manner]
        family=[kind,v.key,features['modality'],features['agent_number'],features['patient_number'],features['polarity']]
    elif kind=='passive':
        v=r.choice(PASSIVES);n,adj,op=object_selection(r,v);patient=object_phrase(n,adj,'nom',op)
        a=r.choice(suitable_actors(v,n));aidx=ACTORS.index(a)
        time=r.choice(TIMES[tense]);place=r.choice(action_places(v,n));manner='' if negative else r.choice(manner_options(v))
        by=a.gen+' მიერ';vb=v.passive[ti];vp=('არ ' if negative else '')+vb
        text=surface([time,patient,place,by,manner,vp])
        roles={'agent':by,'patient':patient,'time':time,'place':place,'manner':manner,'verb':vb}
        features={'tense':'past_imperfect' if ti==1 else tense,'patient_number':'plural' if op else 'singular','patient_case':'nom','verb_number':'singular','subject_animacy':'inanimate','voice':'passive','agent_case':'genitive_mier','polarity':'negative' if negative else 'positive'}
        core=[kind,v.key,aidx,n.nom,adj,op,ti,negative];slots=[time,place,manner]
        family=[kind,v.key,tense,features['patient_number'],features['polarity']]
    elif kind=='experiencer':
        key,sg,pl=r.choice(EXPERIENCERS)
        n=r.choice([x for x in NOUNS if x.category in {'document','concept','digital','process'}]);adj=r.choice(adjective_options(n));op=r.random()<.35
        time=r.choice(STATE_TIMES[tense]);patient=object_phrase(n,adj,'nom',op);agent=aform(a,'dat',sp);vb=(pl if sp else sg)[ti]
        text=surface([time,agent,patient,('არ ' if negative else '')+vb])
        roles={'experiencer':agent,'stimulus':patient,'time':time,'verb':vb}
        features={'tense':'past_imperfect' if ti==1 else tense,'experiencer_number':'plural' if sp else 'singular','stimulus_number':'plural' if op else 'singular','experiencer_case':'dat','stimulus_case':'nom','polarity':'negative' if negative else 'positive'}
        core=[kind,key,aidx,sp,n.nom,adj,op,ti,negative];slots=[time]
        family=[kind,key,tense,features['experiencer_number'],features['polarity']]
    elif kind=='possession':
        n=r.choice([x for x in NOUNS if x.category in {'document','object','equipment','household','artifact','digital'} and x.nom not in {'ნაწილი','განყოფილება','კარი','ფანჯარა'}]);adj=r.choice(adjective_options(n));op=r.random()<.35
        if n.nom=='ტანსაცმელი':op=False
        time=r.choice(STATE_TIMES[tense]);patient=object_phrase(n,adj,'nom',op);location=r.choice(storage_places(n,adj))
        pidx=r.randrange(6) if r.random()<.5 else None
        if pidx is None:agent=aform(a,'dat',sp);vb=HAVE[ti][5 if sp else 2]
        else:agent=PRON_DAT[pidx];vb=HAVE[ti][pidx]
        text=surface([time,agent,location,patient,('არ ' if negative else '')+vb])
        roles={'possessor':agent,'possessed':patient,'time':time,'place':location,'verb':vb}
        features={'tense':tense,'possessor_case':'dat','possessed_case':'nom','possessor_number':'plural' if (pidx>=3 if pidx is not None else sp) else 'singular','possessed_number':'plural' if op else 'singular','person':1+(pidx%3) if pidx is not None else 3,'polarity':'negative' if negative else 'positive'}
        core=[kind,aidx if pidx is None else 'p'+str(pidx),sp if pidx is None else pidx>=3,n.nom,adj,op,ti,negative];slots=[time,location]
        family=[kind,tense,str(pidx) if pidx is not None else ('pl' if sp else 'sg'),features['polarity']]
    elif kind=='motion':
        key,sg,pl=r.choice(MOTION);vb=(pl if sp else sg)[ti];agent=aform(a,'nom',sp)
        di=r.randrange(len(DESTINATIONS));destination=DESTINATIONS[di]
        si=r.randrange(len(SOURCES))
        if si==di:si=(si+1)%len(SOURCES)
        source=SOURCES[si] if key in {'go','return'} else ''
        text=surface([time,agent,source,destination,('არ ' if negative else '')+vb])
        roles={'mover':agent,'time':time,'source':source,'destination':destination,'verb':vb}
        features={'tense':tense,'subject_case':'nom','subject_number':'plural' if sp else 'singular','polarity':'negative' if negative else 'positive'}
        core=[kind,key,aidx,sp,ti,negative,source,destination];slots=[time]
        family=[kind,key,tense,features['subject_number'],features['polarity']]
    elif kind in {'dialogue','genitive'}:
        n=r.choice([x for x in NOUNS if x.category in {'document','object','equipment','household','artifact','digital'} and x.nom not in {'ნაწილი','განყოფილება'}]);adj=r.choice(adjective_options(n));op=r.random()<.35
        if n.nom=='ტანსაცმელი':op=False
        time=r.choice(STATE_TIMES[tense]);patient=a.gen+' '+object_phrase(n,adj,'nom',op);location=r.choice(storage_places(n,adj));vb=['არის','იყო','იქნება'][ti]
        if negative:vp='არ '+vb
        else:vp=vb
        statement=surface([time,patient,location,vp])
        if kind=='dialogue':
            question=' '.join([time,patient,'სად',vb])+'?'
            answer=surface([time,patient,location,vb]);text='— '+question+'\n— '+answer;negative=False
        else:text=statement
        roles={'possessor':a.gen,'located':patient,'time':time,'place':location,'verb':vb}
        features={'tense':tense,'modifier_case':'gen','subject_case':'nom','subject_number':'plural' if op else 'singular','subject_animacy':'inanimate','verb_number':'singular','polarity':'negative' if negative else 'positive'}
        core=[kind,aidx,n.nom,adj,op,ti,negative];slots=[time,location]
        family=[kind,tense,features['subject_number'],features['polarity']]
    elif kind=='personal':
        key=r.choice([k for k in PERSONAL if k in VERB_BY_KEY]);v=VERB_BY_KEY[key];pi=r.randrange(6);n,adj,op=object_selection(r,v)
        place=r.choice(action_places(v,n));manner='' if negative else r.choice(manner_options(v));agent=(PRON_ERG if ti==1 else PRON_NOM)[pi];patient=object_phrase(n,adj,'nom' if ti==1 else 'dat',op)
        vb=PERSONAL[key][ti][pi];text=assemble_clause(time,agent,patient,place,manner,vb,negative,order)
        roles={'agent':agent,'patient':patient,'time':time,'place':place,'manner':manner,'verb':vb}
        features={'tense':tense,'person':pi%3+1,'agent_number':'plural' if pi>=3 else 'singular','agent_case':'erg' if ti==1 else 'nom','patient_number':'plural' if op else 'singular','patient_case':'nom' if ti==1 else 'dat','polarity':'negative' if negative else 'positive'}
        core=[kind,key,pi,n.nom,adj,op,ti,negative];slots=[time,place,manner]
        family=[kind,key,tense,str(pi),features['patient_number'],features['polarity'],str(order)]
    else:raise ValueError(kind)
    return {'text_ka':text,'origin':'rule_synthetic','construction':kind,'rule_family':':'.join(family),'domain':'mobility' if kind=='motion' else n.domain,'features':features,'roles':roles},core,slots

def assert_constructed(row):
    text=row['text_ka'];f=row['features'];k=row['construction'];roles=row['roles']
    assert text.endswith('.') and '  ' not in text and '<' not in text and '@' not in text
    assert all(c.isalpha() and 'ა'<=c<='ჰ' or c in ' .,?!—\n' for c in text)
    if k in {'active','relative','personal'}:
        past=f['tense']=='past'
        assert f['agent_case']==('erg' if past else 'nom')
        assert f['patient_case']==('nom' if past else 'dat')
        assert roles['agent'] in text and roles['patient'] in text
    if k=='passive':assert f['patient_case']=='nom' and f['verb_number']=='singular'
    if k=='modal':assert f['agent_case']==('dat' if f['modality']=='ability' else 'erg') and f['patient_case']=='nom'
    if k=='motion':assert f['subject_case']=='nom'
    if k=='experiencer':assert f['experiencer_case']=='dat' and f['stimulus_case']=='nom'
    if k=='possession':assert f['possessor_case']=='dat' and f['possessed_case']=='nom'
    if f['polarity']=='negative':assert ' არ ' in ' '+text
    return True

def conditional_sample(r):
    first,second=r.choice([('read','check'),('check','correct'),('prepare','send'),('write','read')])
    v1,v2=VERB_BY_KEY[first],VERB_BY_KEY[second]
    common=[n for n in v1.objects if n.nom in {x.nom for x in v2.objects}]
    n=r.choice(common);adj=r.choice(adjective_options(n));op=r.random()<.35
    a=r.choice(ACTORS);sp=r.random()<.4;agent=actor_form(a,'nom',sp);patient=object_phrase(n,adj,'dat',op)
    time=r.choice(TIMES['future']);place=r.choice(action_places(v2,n));manner=r.choice(manner_options(v1))
    vb1=(v1.plural if sp else v1.singular)[2];vb2=(v2.plural if sp else v2.singular)[2]
    pron='ისინი' if sp else 'ის';ref='ამ '+(n.plural_dat if op else n.dat)
    text='თუ '+surface([agent,patient,manner,vb1])[:-1]+', '+surface([time,pron,place,ref,'უფრო ადვილად',vb2])
    features={'tense':'future_conditional','agent_number':'plural' if sp else 'singular','patient_number':'plural' if op else 'singular','agent_case':'nom','patient_case':'dat','polarity':'positive','followup_verb_key':second}
    row={'text_ka':text,'origin':'rule_synthetic','construction':'conditional','rule_family':':'.join(['conditional',first,second,features['agent_number'],features['patient_number']]),'domain':n.domain,'features':features,
      'roles':{'agent':agent,'patient':patient,'time':time,'place':place,'manner':manner,'verb':vb1}}
    core=['conditional',first,second,a.nom,sp,n.nom,adj,op]
    assert_constructed(row);return row,core

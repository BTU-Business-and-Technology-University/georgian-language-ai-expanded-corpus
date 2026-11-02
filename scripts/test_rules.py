#!/usr/bin/env python3
"""Adversarial smoke tests for this controlled grammar implementation."""
import copy,json,random
from pathlib import Path
from grammar import *

def main():
    p=Path(__file__).resolve().parents[1]/'rules/lexical_grounding.json';apply_grounding(json.loads(p.read_text()))
    irregular={'ფურცელი':'ფურცლები','ფანქარი':'ფანქრები','ჩანგალი':'ჩანგლები','ფიცარი':'ფიცრები','კალამი':'კალმები','მიზანი':'მიზნები','დერეფანი':'დერეფნები','ნაჭერი':'ნაჭრები','ფანჯარა':'ფანჯრები','მსხალი':'მსხლები','პომიდორი':'პომიდვრები'}
    for k,v in irregular.items():assert BY_NOM[k].plural==v
    assert PERSONAL['read'][1][0]=='წავიკითხე';assert PERSONAL['read'][2][5]=='წაიკითხავენ'
    assert actor_form(ACTORS[0],'erg',False)=='მასწავლებელმა';assert actor_form(ACTORS[0],'dat',True)=='მასწავლებლებს'
    n=BY_NOM['წიგნი'];assert object_phrase(n,('ახალი','ახალ'),'dat',False)=='ახალ წიგნს';assert object_phrase(n,('ახალი','ახალ'),'nom',False)=='ახალი წიგნი'
    assert all(x not in storage_places(BY_NOM['სკამი']) for x in ['საქაღალდეში','ჩანთაში','ყუთში'])
    assert all(ad[0]!='მოკლე' for ad in adjective_options(BY_NOM['კარტოფილი']))
    r=random.Random(1918);seen=set()
    for i in range(100000):
        row,_,_=sample(r,r.choice(KINDS));assert_constructed(row);seen.add(row['construction'])
        if row['construction']=='active' and row['features']['tense']=='past':
            bad=copy.deepcopy(row);bad['features']['agent_case']='nom'
            try:assert_constructed(bad)
            except AssertionError:pass
            else:raise AssertionError('Wrong aorist case was accepted')
    assert seen==set(KINDS)
    print('PASS: 100000 construction checks, irregular plurals, personal paradigms, physical containment and deliberate case mutation')
if __name__=='__main__':main()

#!/usr/bin/env python3
"""Regression tests for the independently discovered defects and export policy."""
import ctypes,gzip,json,pathlib,subprocess,sys,tempfile,unittest
from export_training import examples
from io_utils import open_text
from split_policy import row_split
ROOT=pathlib.Path(__file__).resolve().parents[1]

class RevisionTests(unittest.TestCase):
 def test_guard_final_line_and_reload(self):
  with tempfile.TemporaryDirectory() as td:
   d=pathlib.Path(td);source=ROOT/'scripts/source_overlap_guard.cpp';exe=d/'guard';lib=d/'guard.so'
   subprocess.run(['c++','-std=c++17','-O2',str(source),'-lz','-o',str(exe)],check=True,capture_output=True)
   flags=['-dynamiclib'] if sys.platform=='darwin' else ['-shared','-fPIC']
   subprocess.run(['c++','-std=c++17','-O2',*flags,str(source),'-lz','-o',str(lib)],check=True,capture_output=True)
   text='მასწავლებელი დღეს სკოლაში ახალ წიგნს ყურადღებით და მშვიდად კითხულობს'
   for filename,content in [('positive','doc\t'+text),('empty','')]:
    with gzip.open(d/(filename+'.gz'),'wt') as f:f.write(content)
    subprocess.run([str(exe),str(d/(filename+'.gz')),str(d/(filename+'.bin'))],check=True,capture_output=True)
   g=ctypes.CDLL(str(lib));g.load_index.argtypes=[ctypes.c_char_p];g.contains_source_8gram.argtypes=[ctypes.c_char_p]
   self.assertEqual(g.load_index(str(d/'positive.bin').encode()),1)
   self.assertEqual(g.contains_source_8gram(text.encode()),1)
   self.assertEqual(g.load_index(str(d/'empty.bin').encode()),1)
   self.assertEqual(g.contains_source_8gram(text.encode()),0)
   self.assertEqual(g.load_index(str(d/'missing.bin').encode()),0)
   self.assertEqual(g.contains_source_8gram(text.encode()),-1)
 def test_export_modes_splits_and_no_overwrite(self):
  manifest=json.loads((ROOT/'data_manifest.json').read_text())
  with tempfile.TemporaryDirectory() as td:
   for mode in ['text','role_qa','case_correction']:
    for split in ['train','validation','test']:
     output=pathlib.Path(td)/(mode+'_'+split+'.gz')
     cmd=[sys.executable,str(ROOT/'scripts/export_training.py'),str(ROOT),'--mode',mode,'--split',split,'--limit','8','--output',str(output)]
     result=subprocess.run(cmd,capture_output=True,text=True)
     self.assertEqual(result.returncode,0,result.stderr)
     self.assertEqual(json.loads(result.stdout)['records_exported'],8)
     before=output.read_bytes()
     self.assertNotEqual(subprocess.run(cmd,capture_output=True).returncode,0)
     self.assertEqual(before,output.read_bytes())
     with gzip.open(output,'rt') as f:
      if mode!='text':
       for line in f:self.assertEqual(len(json.loads(line)['messages']),2)
if __name__=='__main__':unittest.main()

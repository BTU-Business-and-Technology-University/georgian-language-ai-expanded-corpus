#include <algorithm>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <zlib.h>
using namespace std;
static const uint64_t B=0x9e3779b185ebca87ULL;
static const uint64_t MASK=(1ULL<<31)-1;
static const size_t BYTES=(1ULL<<28);
static uint8_t* mapped=nullptr;
static uint64_t mix(uint64_t z){z=(z^(z>>30))*0xbf58476d1ce4e5b9ULL;z=(z^(z>>27))*0x94d049bb133111ebULL;return z^(z>>31);}
static uint64_t wordhash(const string&s){uint64_t h=1469598103934665603ULL;for(unsigned char c:s){h^=c;h*=1099511628211ULL;}return h;}
static bool has(uint64_t h){uint64_t a=mix(h),b=mix(h^0x51ed270b874e6d45ULL)|1ULL;for(int k=0;k<4;k++){auto p=(a+k*b)&MASK;if(!(mapped[p>>3]&(1u<<(p&7))))return false;}return true;}
static void add(uint64_t h,vector<uint8_t>&bits){uint64_t a=mix(h),b=mix(h^0x51ed270b874e6d45ULL)|1ULL;for(int k=0;k<4;k++){auto p=(a+k*b)&MASK;bits[p>>3]|=uint8_t(1u<<(p&7));}}
template<class F>static void grams(const string&s,F fn){
 uint64_t ring[8]={},rolling=0,power=1;for(int i=0;i<7;i++)power*=B;
 int size=0,pos=0;string word;
 auto flush=[&](){if(word.empty())return;auto h=wordhash(word);word.clear();if(size<8){rolling=rolling*B+h;ring[size++]=h;if(size==8)fn(rolling);}else{rolling=(rolling-ring[pos]*power)*B+h;ring[pos]=h;pos=(pos+1)%8;fn(rolling);}};
 for(size_t i=0;i<s.size();){unsigned char a=s[i];if(i+2<s.size()&&a==0xe1&&(unsigned char)s[i+1]==0x83&&(unsigned char)s[i+2]>=0x90&&(unsigned char)s[i+2]<=0xb0){word.append(s,i,3);i+=3;}else{flush();i++;}}
 flush();
}
extern "C" int load_index(const char*path){if(mapped){munmap(mapped,BYTES);mapped=nullptr;}int fd=open(path,O_RDONLY);if(fd<0)return 0;struct stat st;if(fstat(fd,&st)||size_t(st.st_size)!=BYTES){close(fd);return 0;}void*p=mmap(nullptr,BYTES,PROT_READ,MAP_SHARED,fd,0);close(fd);if(p==MAP_FAILED)return 0;mapped=(uint8_t*)p;return 1;}
extern "C" int contains_source_8gram(const char*text){if(!mapped)return -1;bool matched=false;grams(string(text),[&](uint64_t h){if(!matched&&has(h))matched=true;});return matched?1:0;}
int main(int argc,char**argv){
 if(argc!=3){cerr<<"source_overlap_guard PRIVATE_CORPUS.tsv.gz PRIVATE_INDEX.bin\n";return 2;}
 vector<uint8_t> bits(BYTES);gzFile f=gzopen(argv[1],"rb");if(!f)return 3;gzbuffer(f,1<<20);string buffer;char chunk[1<<18];uint64_t docs=0,count=0;
 while(true){int n=gzread(f,chunk,sizeof(chunk));if(n<0)return 4;if(n==0)break;buffer.append(chunk,n);size_t start=0,end;
  while((end=buffer.find('\n',start))!=string::npos){string line=buffer.substr(start,end-start);auto tab=line.find('\t');if(tab!=string::npos)line.erase(0,tab+1);grams(line,[&](uint64_t h){add(h,bits);count++;});docs++;start=end+1;if(docs%50000==0)cerr<<"indexed documents "<<docs<<" windows "<<count<<"\n";}
  buffer.erase(0,start);
 }
 if(!buffer.empty()){auto tab=buffer.find('\t');if(tab!=string::npos)buffer.erase(0,tab+1);grams(buffer,[&](uint64_t h){add(h,bits);count++;});docs++;}
 if(gzclose(f)!=Z_OK)return 5;ofstream out(argv[2],ios::binary);out.write((char*)bits.data(),bits.size());out.close();if(!out)return 6;cerr<<"FINAL documents "<<docs<<" eight-word windows "<<count<<" bytes "<<bits.size()<<"\n";
}

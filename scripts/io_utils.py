"""Streaming readers and atomic, in-memory publication of compressed shards."""
from contextlib import contextmanager
import gzip,hashlib,io,os,tempfile,shutil,subprocess
from pathlib import Path

@contextmanager
def open_text(path):
    path=Path(path)
    if path.suffix=='.gz':
        with gzip.open(path,'rt',encoding='utf-8') as f:yield f
    elif path.suffix=='.zst':
        try:
            import zstandard
        except ImportError:
            executable = os.environ.get('ZSTD_BIN') or shutil.which('zstd')
            if not executable:
                raise RuntimeError('Install zstandard or provide zstd on PATH / ZSTD_BIN')
            process = subprocess.Popen([executable, '-dc', str(path)], stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE, text=True, encoding='utf-8')
            completed = False
            try:
                yield process.stdout
                # Drain when a caller intentionally reads a prefix; still check integrity.
                for _ in process.stdout: pass
                error = process.stderr.read()
                code = process.wait()
                completed = True
                if code:
                    raise IOError('Zstandard decoding failed: ' + error)
            finally:
                process.stdout.close()
                process.stderr.close()
                if not completed:
                    process.terminate()
                    process.wait()
        else:
            with path.open('rb') as raw:
                with zstandard.ZstdDecompressor().stream_reader(raw) as reader:
                    with io.TextIOWrapper(reader,encoding='utf-8') as text:yield text
    else:
        with path.open('r',encoding='utf-8') as f:yield f

def write_bytes_atomic(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);expected=hashlib.sha256(data).digest()
    for attempt in range(3):
        fd,tmp=tempfile.mkstemp(prefix='.commit-',dir=path.parent)
        try:
            with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
            os.replace(tmp,path)
            if hashlib.sha256(path.read_bytes()).digest()==expected:return
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
    raise IOError('Published bytes failed checksum: '+str(path))

"""Read PostgreSQL .dat catalog literals without executing Perl or SQL."""
import re

def records(text):
    start=None;depth=0;quoted=False;escape=False;comment=False
    for pos,ch in enumerate(text):
        if comment:
            if ch=='\n':comment=False
            continue
        if quoted:
            if escape:escape=False
            elif ch=='\\':escape=True
            elif ch=="'":quoted=False
            continue
        if ch=='#':comment=True;continue
        if ch=="'":quoted=True;continue
        if ch=='{':
            if depth==0:start=pos
            depth+=1
        elif ch=='}':
            depth-=1
            if depth==0 and start is not None:
                raw=text[start:pos+1]
                fields={key:value.replace("\\'","'").replace('\\\\','\\') for key,value in re.findall(r"(\w+)\s*=>\s*'((?:\\.|[^'\\])*)'",raw)}
                yield {**fields,'_source_start':start,'_source_end':pos+1,'_raw':raw}
                start=None
    if depth or quoted:raise ValueError('Unclosed catalog literal')

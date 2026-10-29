"""Authorized one-time narration run, with a persistent $2 usage guard.

Reads only the explicitly authorized OPENAI_API_KEY assignment in ~/.zshrc.
Never sources the shell profile, prints the key, or writes credentials.
"""
import argparse,asyncio,fcntl,json,os,re,shlex
from decimal import Decimal
from pathlib import Path
import build_openai_narration as b

ROOT=Path(__file__).resolve().parent.parent
LEDGER=ROOT/'output/openai-narration-usage.json'
LIMIT=Decimal('2.00')
RESERVE=Decimal('0.035')


def cost(usage):
    if not usage or 'input_tokens' not in usage or 'output_tokens' not in usage:
        return RESERVE
    inp=usage.get('input_token_details',{})
    out=usage.get('output_token_details',{})
    # No audio input is sent. Use higher audio rates if unexpected audio appears.
    audio_in=inp.get('audio_tokens',0)
    audio_out=out.get('audio_tokens',usage['output_tokens'])
    return (Decimal(str(audio_in))*10 + Decimal(str(max(0,usage['input_tokens']-audio_in)))*Decimal('.60') + Decimal(str(audio_out))*20 + Decimal(str(max(0,usage['output_tokens']-audio_out)))*Decimal('2.40'))/1000000


def authorized_key():
    if os.environ.get('OPENAI_API_KEY'):
        return os.environ['OPENAI_API_KEY']
    for line in (Path.home()/'.zshrc').read_text().splitlines():
        match=re.match(r'^\s*(?:export\s+)?OPENAI_API_KEY\s*=\s*(.+)$',line)
        if match:
            parts=shlex.split(match.group(1),comments=True)
            if len(parts)==1 and '$' not in parts[0] and '`' not in parts[0]:
                return parts[0]
    raise b.BuildError('Authorized key assignment was not found; no other credential sources were searched')


async def run(sample=False):
    LEDGER.parent.mkdir(exist_ok=True,parents=True)
    with LEDGER.with_suffix('.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        ledger=json.loads(LEDGER.read_text()) if LEDGER.exists() else {'limit_usd':str(LIMIT),'requests':[]}
        api_key=authorized_key()
        async def request_once(spec):
            # Conservative admission check: UTF-8 bytes upper-bound text token count.
            text_bytes=len((spec['instructions']+spec['text']).encode())
            if text_bytes>6000:
                raise b.BuildError('Prompt exceeds conservative request budget bound')
            spent=sum(Decimal(x['charged_or_reserved_usd']) for x in ledger['requests'])
            if spent+RESERVE>LIMIT:
                raise b.BuildError('Two-dollar budget guard stopped before another request')
            row={'index':len(ledger['requests'])+1,'voice':spec['voice'],'text':spec['text'],'charged_or_reserved_usd':str(RESERVE),'status':'reserved'}
            ledger['requests'].append(row)
            b.write_json_atomic(LEDGER,ledger)
            def usage_done(usage):
                row.update(usage=usage,charged_or_reserved_usd=str(cost(usage)),status='billed')
                b.write_json_atomic(LEDGER,ledger)
            try:
                return await b.render_realtime(spec,api_key=api_key,usage_callback=usage_done)
            except b.BuildError as exc:
                if hasattr(exc,'actual_transcript'):
                    row['rejected_transcript']=exc.actual_transcript
                    row['validation']='rejected'
                    b.write_json_atomic(LEDGER,ledger)
                raise
        async def renderer(spec):
            for attempt in range(3):
                try:
                    return await request_once(spec)
                except b.BuildError as exc:
                    if not hasattr(exc,'actual_transcript') or attempt==2:
                        raise
                    print('Retaking wording mismatch; usage remains counted',flush=True)
        args=argparse.Namespace(sample='tutorial:beat:0' if sample else None,dry_run=False,check=False,activate=not sample)
        try:
            await b.build(args,renderer=renderer)
        finally:
            total=sum(Decimal(x['charged_or_reserved_usd']) for x in ledger['requests'])
            ledger['total_charged_or_reserved_usd']=str(total)
            b.write_json_atomic(LEDGER,ledger)
            print('Usage total USD:',total,flush=True)

if __name__=='__main__':
    import sys
    try:
        asyncio.run(run('--sample' in sys.argv))
    except b.BuildError as exc:
        print('Narration stopped:',exc,file=sys.stderr)
        sys.exit(1)

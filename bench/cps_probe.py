"""Read-only AnyTone programming probe over the running firmware USB bridge."""
import argparse,hashlib,json,struct,time
from pathlib import Path
from cps_bridge import Client


def check_read(response,address):
    if len(response)!=24 or response[:1]!=b'W' or response[1:5]!=struct.pack('>I',address) or response[5]!=16 or response[-1]!=6:
        raise ValueError('Invalid memory read response')
    if sum(response[1:-2])&255!=response[-2]:raise ValueError('Memory read checksum mismatch')
    return response[6:22]


def probe(client,address=0x02FA0000):
    start=time.monotonic();client.connect();enumerated=time.monotonic()
    identity=client.prepare();identified=time.monotonic()
    response=client.exchange(b'R'+struct.pack('>I',address)+b'\x10',24)
    data=check_read(response,address)
    return dict(passed=True,server_url=client.url,server_application=client.server_application,model=identity[1:8].rstrip(b'\0').decode('ascii',errors='replace'),
        identity_hex=identity.hex(),read_address=f'0x{address:08X}',read_bytes=16,read_SHA256=hashlib.sha256(data).hexdigest(),
        enumeration_seconds=enumerated-start,program_and_identity_seconds=identified-enumerated,
        memory_read_seconds=time.monotonic()-identified,responses_source='executed firmware PMA',
        memory_writes_requested=False,programming_mode_left_active=True,original_CPS_executed=False)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--url',help='Adresse du banc, détectée automatiquement par défaut');parser.add_argument('--read-address',type=lambda v:int(v,0),default=0x02FA0000)
    args=parser.parse_args();client=None
    try:
        client=Client(args.url);print(json.dumps(probe(client,args.read_address),indent=2))
    except Exception as error:
        diagnostic=client.diagnostic() if client else {}
        diagnostic['error']=str(error);target=Path(__file__).resolve().parent/'results/cps_probe_diagnostic.json'
        try:
            target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(diagnostic,indent=2),encoding='utf-8')
            detail='\nDiagnostic : '+str(target)
        except OSError:detail=''
        parser.exit(1,'USB probe failed: '+str(error)+detail+'\n')

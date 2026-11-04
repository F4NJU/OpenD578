"""Explicit OEM observation anchors, separate from peripheral bus models.

Matching these bytes permits these observations only. It does not establish the
ABI or correctness of a changed application, or qualify it for physical use.
"""
import hashlib,json,argparse
from pathlib import Path
from audit_ram_v121 import APP,EXPECTED_SHA

HOOKS={
    0x08006D3C:'SystemInit checkpoint',0x0800620C:'scatter checkpoint',
    0x08006654:'main checkpoint',0x080899F2:'clock checkpoint',
    0x08006668:'GPIO checkpoint',0x0800666C:'SysTick checkpoint',
    0x0808AE62:'NAND ID checkpoint',0x0808ADBE:'NAND receive buffer check',
    0x08009F0C:'delay polling acceleration',0x08074736:'date idle acceleration',
    0x0809319E:'date idle acceleration',0x080AD2D8:'RTOS idle acceleration',
    0x0808B672:'LCD command crosscheck and bus arming',
    0x0808A7C0:'lighting bus arming',0x08088876:'software I2C crosscheck',
    0x080A2AA4:'SCT boot source',0x0808AB18:'RF write crosscheck',
    0x0808ABDC:'RF read crosscheck',0x08072426:'fan request observation',
    0x0808BE9C:'fan/PTT observation',0x08074EB4:'TX entry candidate',
    0x0806CD02:'GPS parser observation',0x0806624C:'APRS scheduling',
    0x08066306:'APRS modulation entry',0x0808E522:'GPS UART wait',
    0x0808D86C:'microphone UART wait',0x0808D8A6:'microphone UART wait',
    0x08090B62:'audio path observation',
}

def inspect_profile(reference,selected):
    if hashlib.sha256(reference).hexdigest()!=EXPECTED_SHA:
        raise ValueError('Observation profile requires the authenticated V1.21 reference')
    mismatches=[]
    for address,label in HOOKS.items():
        offset=address-APP;expected=reference[offset:offset+16];actual=selected[offset:offset+16]
        if len(actual)!=16 or actual!=expected:
            mismatches.append(dict(address=hex(address),purpose=label,
                reference_sha256=hashlib.sha256(expected).hexdigest(),
                selected_sha256=hashlib.sha256(actual).hexdigest()))
    exact=selected==reference
    return dict(profile='D578_PRO_GD32_V1.21',anchor_count=len(HOOKS),
        anchor_bytes=16,anchors_compatible=not mismatches,mismatches=mismatches,
        reference_application_sha256=EXPECTED_SHA,
        selected_application_sha256=hashlib.sha256(selected).hexdigest(),
        OEM_RAM_ABI_qualified=exact,modified_firmware_certified=False,
        limitation='Anchor matching cannot prove the ABI or behavior of modified code')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference',type=Path);parser.add_argument('selected',type=Path)
    args=parser.parse_args()
    from firmware_input import inspect_image
    report=inspect_profile(inspect_image(args.reference)[1],inspect_image(args.selected)[1])
    print(json.dumps(report,indent=2));raise SystemExit(0 if report['anchors_compatible'] else 2)

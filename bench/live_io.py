"""Best-effort atomic status publication despite short Windows reader locks."""
import json,time
def publish_status(target,value,final=False):
    temporary=target.with_suffix('.tmp.json')
    try:temporary.write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8')
    except OSError:return False
    for attempt in range(30 if final else 4):
        try:temporary.replace(target);return True
        except PermissionError:
            if attempt+1<(30 if final else 4):time.sleep(.002)
    # The next periodic publication retries. A UI reader must never crash CPU
    # execution; the final result is also saved separately by run_lcd.py.
    return False

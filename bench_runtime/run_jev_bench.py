from pathlib import Path
import hashlib,json,os,sys,traceback
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.r3_clm_redfrag_benchmark import run
fixture=ROOT/"tests"/"redfrag_benchmark_v1.json"
expected="0cff14f3cfb64650d955ffedd227a875978e6682ccd653b1f78b112685bd127f"
actual=hashlib.sha256(fixture.read_bytes()).hexdigest()
run_id=os.getenv("R3_JEV_BENCH_RUN_ID","unknown")
print("OMEE_REDFRAG_JEV_START "+json.dumps({"run_id":run_id,"fixture_sha256":actual,"expected":expected,"ok":actual==expected},sort_keys=True),flush=True)
if actual!=expected: raise SystemExit(3)
for view in ("flags","blind"):
    try:
        report=run(fixture,repeats=20,provider="typesafe",view=view)
        print("OMEE_REDFRAG_JEV_RESULT "+json.dumps({"run_id":run_id,"view":view,"report":report},ensure_ascii=False,separators=(",",":")),flush=True)
    except Exception as exc:
        print("OMEE_REDFRAG_JEV_ERROR "+json.dumps({"run_id":run_id,"view":view,"error":type(exc).__name__,"detail":str(exc)[:300]},ensure_ascii=False),flush=True)
        traceback.print_exc(); raise
print("OMEE_REDFRAG_JEV_DONE "+json.dumps({"run_id":run_id},sort_keys=True),flush=True)

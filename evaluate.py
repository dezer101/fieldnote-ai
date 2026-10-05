"""Run the deterministic retrieval benchmark; no model/API call is required."""
import json
from pathlib import Path
from app import answer_query, retrieve
ROOT = Path(__file__).parent
cases = json.loads((ROOT / "data/evaluation.json").read_text(encoding="utf-8-sig"))
correct = 0
for case in cases["cases"]:
    hits = retrieve(case["question"])
    got = hits[0]["id"] if hits else None
    ok = got == case["expected_source"]
    correct += ok
    print(f"{'PASS' if ok else 'MISS'}  expected={case['expected_source']} retrieved={got}  {case['question']}")
refused = 0
for question in cases["out_of_scope"]:
    result = answer_query(question)
    did_refuse = not result["sources"]
    refused += did_refuse
    print(f"{'PASS' if did_refuse else 'MISS'}  out_of_scope={question}")
print(f"\nTop-1 retrieval: {correct}/{len(cases['cases'])} ({correct/len(cases['cases']):.0%})")
print(f"Out-of-scope abstention: {refused}/{len(cases['out_of_scope'])} ({refused/len(cases['out_of_scope']):.0%})")

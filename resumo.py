"""Resume um teste do Locust: python3 resumo.py resultados/<nome>"""
import csv, re, sys, collections
p = sys.argv[1]
r = [x for x in csv.DictReader(open(f"{p}_stats.csv")) if x["Name"] == "Aggregated"][0]
n = int(r["Request Count"]); f = int(r["Failure Count"])
print(f"{p}: reqs={n} falhas={f} ({100*f/n:.1f}%) rps={float(r['Requests/s']):.1f} "
      f"media={float(r['Average Response Time']):.0f}ms mediana={r['Median Response Time']}ms "
      f"p95={r['95%']}ms p99={r['99%']}ms max={float(r['Max Response Time']):.0f}ms")
c = collections.Counter()
for x in csv.DictReader(open(f"{p}_failures.csv")):
    e = re.sub(r"<HTTPConnection.*?>", "<conn>", x["Error"]); e = re.sub(r"0x[0-9a-f]+", "", e)
    c[e] += int(x["Occurrences"])
for k, v in c.most_common(6): print(f"   {v:>7}  {k[:110]}")

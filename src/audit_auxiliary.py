"""Audit members and a listening-log release using aggregate SQL outputs."""
import argparse
import hashlib
import json
from pathlib import Path
import duckdb


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--members", type=Path, required=True)
    parser.add_argument("--logs", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    con = duckdb.connect(str(args.output_dir / "auxiliary.duckdb"))
    con.execute("SET threads=4")
    con.execute("SET memory_limit='4GB'")
    results = {}
    for table,path in (("members",args.members),("logs",args.logs)):
        print("Loading " + path.name, flush=True)
        con.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM read_csv(?,header=true,all_varchar=true)",[str(path)])
        digest=hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b""):
                digest.update(chunk)
        results[table]={"filename":path.name,"size_bytes":path.stat().st_size,"sha256":digest.hexdigest()}
    cursor=con.execute("""SELECT count(*) row_count,count(DISTINCT msno) customers,
      count(*)-count(DISTINCT msno) duplicate_key_excess,
      count(*) FILTER(WHERE msno IS NULL) missing_ids,
      count(*) FILTER(WHERE gender IS NULL) missing_gender,
      count(*) FILTER(WHERE try_cast(bd AS INTEGER)=0) zero_age,
      count(*) FILTER(WHERE try_cast(bd AS INTEGER)<0 OR try_cast(bd AS INTEGER)>100) age_outside_0_100,
      min(registration_init_time) min_registration_date,max(registration_init_time) max_registration_date,
      count(*) FILTER(WHERE try_strptime(registration_init_time,'%Y%m%d') IS NULL) invalid_registration_dates
      FROM members""")
    results["members"].update(dict(zip([c[0] for c in cursor.description],cursor.fetchone())))
    cursor=con.execute("""SELECT count(*) row_count,count(DISTINCT msno) customers,
      min(date) min_date,max(date) max_date,
      count(*) FILTER(WHERE msno IS NULL OR date IS NULL) missing_keys,
      count(*) FILTER(WHERE try_strptime(date,'%Y%m%d') IS NULL) invalid_dates,
      count(*) FILTER(WHERE try_cast(total_secs AS DOUBLE)<0) negative_listening_seconds,
      count(*) FILTER(WHERE try_cast(total_secs AS DOUBLE)>86400) over_24h_listening_seconds,
      count(*) FILTER(WHERE try_cast(total_secs AS DOUBLE) IS NULL) invalid_listening_seconds
      FROM logs""")
    results["logs"].update(dict(zip([c[0] for c in cursor.description],cursor.fetchone())))
    results["logs"]["duplicate_customer_day_excess"] = con.execute("SELECT coalesce(sum(n-1),0) FROM (SELECT msno,date,count(*) n FROM logs GROUP BY ALL HAVING count(*)>1)").fetchone()[0]
    results["logs"]["customers_without_member_record"] = con.execute("SELECT count(DISTINCT l.msno) FROM logs l WHERE NOT EXISTS (SELECT 1 FROM members m WHERE l.msno=m.msno)").fetchone()[0]
    results["limits"]="Flags identify review populations; they do not justify deletion. Only the named log release is scanned."
    (args.output_dir / "auxiliary_audit.json").write_text(json.dumps(results,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(results,indent=2),flush=True)
    con.close()


if __name__ == "__main__":
    main()

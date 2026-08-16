from __future__ import annotations
import argparse, asyncio, json
from .models import SearchRequest
from .service import ScholarMapService


def main():
    p=argparse.ArgumentParser(description="ScholarMap — find the papers that actually matter")
    p.add_argument("topic")
    p.add_argument("--from",dest="date_from",required=True,help="YYYY-MM")
    p.add_argument("--to",dest="date_to",required=True,help="YYYY-MM")
    p.add_argument("--live",action="store_true")
    p.add_argument("--limit",type=int,default=10)
    args=p.parse_args()
    req=SearchRequest(topic=args.topic,date_from=args.date_from,date_to=args.date_to,live=args.live,papers_per_section=args.limit)
    res=asyncio.run(ScholarMapService().search(req))
    for w in res.warnings: print(f"WARNING: {w}")
    print(f"\n{res.topic} | {res.date_from} → {res.date_to}\n")
    for sec in res.sections:
        print(f"## {sec.title}")
        for i,x in enumerate(sec.papers,1):
            print(f"{i:2d}. {x.title} | {x.venue or 'arXiv/other'} | {x.citations} cites")
        print()

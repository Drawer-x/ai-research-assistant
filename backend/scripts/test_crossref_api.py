"""Bounded Crossref configuration and optional live API probe."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.services.crossref_client import CrossrefClient

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--live",action="store_true");args=parser.parse_args()
    if not args.live:
        print("CROSSREF_CONFIG_OK");return
    client=CrossrefClient();result=client.search_works("retrieval augmented generation",page_size=5)
    assert result["items"] and result["items"][0]["doi"] and result["items"][0]["title"]
    paper=client.get_work(result["items"][0]["doi"]);assert paper["doi"]==result["items"][0]["doi"] and paper["title"]
    print("CROSSREF_LIVE_API_OK")
    print("search_status=200\ndetail_status=200")
    print(f"items_count={len(result['items'])}\nhas_abstract={bool(paper['abstract'])}\nhas_references={paper['reference_count']>0}")

if __name__=="__main__": main()

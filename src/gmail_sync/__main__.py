from __future__ import annotations
import argparse
from .pipeline import fetch_messages

def main() -> None:
    p = argparse.ArgumentParser(description="List Gmail Messages (From/Subject/Date)")

    grp = p.add_mutually_exclusive_group()

    grp.add_argument("--promotions-unread", action="store_true", help="Use query: category:promotions is:unread")

    grp.add_argument("--inbox-unread", action="store_true", help="Use query: in:inbox is:unread")

    grp.add_argument("--inbox-1d", action="store_true", help="Use query: in:inbox newer_than:1d")

    p.add_argument("--q", default=None, help="Custom Gmail search query (overrides presets)")

    p.add_argument("--labels", nargs="*", default=[], help="Label IDs instead of query (e.g. INBOX UNREAD CATEGORY_PROMOTIONS)")

    p.add_argument("--max", type=int, default=10, help="Max results to fetch (<=500)")  

    args = p.parse_args()

    # Pick sensible defaults
    q = args.q
    if q is None:
        if args.promotions_unread:
            q = "category:promotions is:unread"
        elif args.inbox_unread:
            q = "in:inbox is:unread"
        elif args.inbox_1d:
            q = "in:inbox newer_than:1d"
        else:
            q = "category:promotions is:unread"

    rows = fetch_messages(query=q, label_ids=args.labels, max_results=args.max)

    if not rows:
        print("No messages found.")
        return

    w_date = max(4, max(len(r["Date"]) for r in rows))
    w_from = max(4, max(len(r["From"]) for r in rows))
    header = f"{'Date':<{w_date}}  {'From':<{w_from}}  Subject"
    print(header)   
    print("-" * len(header))
    for r in rows:
        print(f"{r['Date']:<{w_date}}  {r['From']:<{w_from}}  {r['Subject']}")

if __name__ == "__main__":
    main() 

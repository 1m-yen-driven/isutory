from argparse import ArgumentParser
from collections import Counter
import re
from networkx import DiGraph
from networkx.algorithms.isomorphism import DiGraphMatcher
from networkx.drawing.nx_pydot import to_pydot
from pprint import pprint

# global keys
URI = 'uri'
METHOD = 'method'
TIME = 'time'
UA = "ua"
VHOST = "vhost"
APPTIME = "apptime"
REQTIME = "reqtime"
STATUS = "status"
SIZE = "size"
KEYS = [URI, METHOD, TIME, UA, VHOST, APPTIME, REQTIME, STATUS, SIZE]
IDENTIFIER = 'ua'

###  PARSE DATA
def load_data(path):
    data = []
    with open(path) as f:
        for line in f:
            data.append(
                {
                    k: v for k, v in map(
                        lambda x: x.split(':', 1),
                        line.strip().split('\t')
                    )
                    if k in KEYS
                }
            )
    return data

def is_ignored(uri, ignore):
    for i in ignore:
        if i and i.match(uri):
            return True
    return False

def filter_ignored_uri(data, ignore):
    ignore = [re.compile(i) for i in ignore if i]
    return list(filter(lambda d: not is_ignored(d[URI], ignore), data))

def unify_uri(uri, aggregates):
    for a in aggregates:
        if a.match(uri):
            return a.pattern
    return uri

def aggregate(data, aggregates):
    aggregates = [re.compile(a) for a in aggregates if a]
    hits = {}
    for i in range(len(data)):
        raw = data[i][URI]
        unified = unify_uri(raw, aggregates)
        data[i][URI] = unified
        if not (unified in hits):
            hits[unified] = set()
        hits[unified].add(raw)
    hitdata = {}
    for k, v in hits.items():
        hitdata[k] = len(v)
    return data, hitdata


### CREATE STORY GRAPH
class IDGenerator:
    def __init__(self):
        self._dict = dict()
        self._cnt = 0

    def __getitem__(self, key):
        if key not in self._dict:
            self._dict[key] = self._cnt
            self._cnt += 1
        return self._dict[key]

_id = IDGenerator()

def node(r, cnt=0):
    """node returns node's name.

    pydot doesn't escape names of nodes for DOT, so it's better to convert URI to integers.
    """
    return _id["%d:%s" % (cnt, r)]

def req(t):
    return "%s %s" % (t[0], t[1])

def create_story(timeline, story_id):
    t = timeline
    sid = story_id
    s = DiGraph()
    r = req(t[0])
    n = node(r, sid)
    s.add_node(n, label=r)
    for d1, d2 in zip(t, t[1:]):
        r1 = req(d1)
        n1 = node(r1, sid)
        r2 = req(d2)
        n2 = node(r2, sid)
        s.add_node(n2, label=r2)
        s.add_edge(n1, n2)
    return s

def create_stories(data):
    timelines = dict()
    for d in data:
        nodes, timeline = timelines.get(d[IDENTIFIER], (set(), list()))
        t = (d[METHOD], d[URI], d[TIME])
        nodes.add(req(t))
        timeline.append(t)
        timelines[d[IDENTIFIER]] = (nodes, timeline)
    for k in timelines.keys():
        timelines[k][1].sort(key=lambda t: t[2])
    stories = DiGraph()
    cnt = 0
    for _, t in sorted(timelines.values(), key=lambda t: len(t[0]), reverse=True):
        if len(t) == 0:
            continue
        s = create_story(t, cnt)
        dm = DiGraphMatcher(stories, s, node_match=lambda a, b: a['label'] == b['label'])
        if not dm.subgraph_is_isomorphic():
            stories.add_nodes_from(s.nodes.data())
            stories.add_edges_from(s.edges)
            cnt += 1
    return stories

def create_unified_graph(data):
    timelines = dict()
    for d in data:
        timeline = timelines.get(d[IDENTIFIER], list())
        t = (d[METHOD], d[URI], d[TIME])
        timeline.append(t)
        timelines[d[IDENTIFIER]] = timeline
    src = dict()
    for timeline in timelines.values():
        timeline.sort(key=lambda t: t[2])
        if len(timeline) < 2:
            continue
        for t1, t2 in zip(timeline, timeline[1:]):
            r1 = req(t1)
            r2 = req(t2)
            total, dst = src.get(r1, (0, Counter()))
            dst[r2] += 1
            src[r1] = (total + 1, dst)
    stories = DiGraph()
    for f, (total, dst) in src.items():
        nf = node(f)
        stories.add_node(nf, label=f)
        for t, cnt in dst.items():
            nt = node(t)
            stories.add_node(nt, label=t)
            stories.add_edge(nf, nt, color="#000000%02X" % (16 + 240 * cnt // total))
    return stories

def write_graph(stories, out):
    pd = to_pydot(stories)
    if out.endswith(".svg") or out.endswith(".html"):
        pd.write_svg(out)
    elif out.endswith(".dot"):
        pd.write_dot(out)
    elif out.endswith(".png"):
        pd.write_png(out)
    else:
        raise ValueError("unexpected extension: %s" % out)

### STATISTICS MODE
def show_statistics(data, hitdata):
    # show variation counts
    by_key = {}
    for d in data:
        for k, v in d.items():
            if not (k in by_key):
                by_key[k] = {}
            if not (v in by_key[k]):
                by_key[k][v] = 0
            by_key[k][v] += 1
    def print_formatted_data(key, value_len, print_count, hit=False):
        results = []
        for k, v in by_key[key].items():
            results.append([k, v])
        results.sort(key = lambda x: x[1], reverse=True)
        print(f"{len(data)} (100.0%) : *")
        for value, count in results[:print_count]:
            if len(value) >= value_len:
                half = int(value_len / 2)
                name = value[:half] + "..." + value[len(value) - half:]
            else:
                name = value
            percent = f"{100*count/len(data):.1f}"
            if hit and hitdata[value] > 1:
                print(f"{count} ({percent}%) :", name, f"({hitdata[value]})")
            else:
                print(f"{count} ({percent}%) :", name)
        if len(results) > print_count:
            print("...")
    print(f"### USER AGENT ({len(by_key[UA])}) ###")
    print_formatted_data(UA, 30, 10)
    print(f"\n### STATUS ({len(by_key[STATUS])}) ###")
    print_formatted_data(STATUS, 30, 100)
    print(f"\n### URI ({len(by_key[URI])}) ###")
    print_formatted_data(URI, 50, 100, True)
    # print("\n### TIME & SIZE ###")
    # SIZE, APPTIME, REQTIME

def main(args):
    data = load_data(args.ltsv)
    if len(args.ignore) == 1:
        args.ignore = args.ignore[0].split(',')
    else:
        args.ignore = [""]
    data = filter_ignored_uri(data, args.ignore)
    if len(args.aggregates) == 1:
        args.aggregates = args.aggregates[0].split(',')
    data, hitdata = aggregate(data, args.aggregates)
    if args.statistics:
        show_statistics(data, hitdata)
        return
    if args.unified:
        stories = create_unified_graph(data)
    else:
        stories = create_stories(data)
    write_graph(stories, args.out)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('ltsv', help='nginx log formatted in LTSV')
    parser.add_argument('--aggregates', default="", nargs='*', help='URL aggregation')
    parser.add_argument('--ignore', default="", nargs='*', help='URL to ignore')
    parser.add_argument('--unified', action='store_true', help='show unified graph which highlights where to go')
    parser.add_argument('--identifier', default=IDENTIFIER, help='label of user identifier')
    parser.add_argument('--statistics', action="store_true", help='use statistics mode')
    parser.add_argument('--out', default='stories.svg', help='name of output svg file')
    args = parser.parse_args()
    IDENTIFIER = args.identifier
    main(args)

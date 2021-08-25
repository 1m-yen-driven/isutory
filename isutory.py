from argparse import ArgumentParser
import re
from networkx import DiGraph
from networkx.algorithms.isomorphism import DiGraphMatcher
from networkx.drawing.nx_pydot import to_pydot

URI = 'uri'
METHOD = 'method'
TIME = 'time'
USER = 'ua'

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

def load_data(path, necessary_keys):
    data = []
    with open(path) as f:
        for line in f:
            data.append(
                {
                    k: v for k, v in map(
                        lambda x: x.split(':', 1),
                        line.strip().split('\t')
                    )
                    if k in necessary_keys
                }
            )
    return data

def unify_uri(uri, aggregates):
    for a in aggregates:
        if a.match(uri):
            return a.pattern
    return uri

def req(t):
    return "%s %s" % (t[0], t[1])

def node(r, cnt):
    """node returns node's name.
    
    pydot doesn't escape names of nodes for DOT, so it's better to convert URI to integers.
    """
    return _id["%d:%s" % (cnt, r)]

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
        nodes, timeline = timelines.get(d[USER], (set(), list()))
        t = (d[METHOD], d[URI], d[TIME])
        nodes.add(req(t))
        timeline.append(t)
        timelines[d[USER]] = (nodes, timeline)
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

def show_graph(stories, out):
    pd = to_pydot(stories)
    if out.endswith(".svg"):
        pd.write_svg(out)
    elif out.endswith(".dot"):
        pd.write_dot(out)
    elif out.endswith(".png"):
        pd.write_png(out)
    else:
        raise ValueError("unexpected extension: %s" % out)

def main(args):
    data = load_data(args.ltsv, [URI, METHOD, TIME, USER])
    if len(args.aggregates) == 1:
        args.aggregates = args.aggregates[0].split(',')
    aggregates = [re.compile(a) for a in args.aggregates]
    for i in range(len(data)):
        data[i][URI] = unify_uri(data[i][URI], aggregates)
    stories = create_stories(data)
    show_graph(stories, args.out)

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('ltsv', help='nginx log formatted in LTSV')
    parser.add_argument('--aggregates', nargs='*', help='URL aggregation')
    parser.add_argument('--out', '-o', default='stories.svg', help='name of output svg file')
    args = parser.parse_args()
    main(args)

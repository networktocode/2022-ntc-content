import logging
import sys

from pybatfish.client import asserts
from pybatfish.client.commands import bf_session
from pybatfish.datamodel.flow import HeaderConstraints
from pybatfish.question import load_questions

logging.getLogger("pybatfish").setLevel(logging.WARN)
SNAPSHOT_DIR = '/local/data'


def setup():
    bf_session.host = "batfish"
    load_questions()
    bf_session.set_network('webinar')
    bf_session.init_snapshot(SNAPSHOT_DIR, name='snapshot-1', overwrite=True)
    print("=" * 20)
    print("Starting Batfish Setup.....")
    print("=" * 20)


def test_protocols(assertion_str):
    result = getattr(asserts, assertion_str)()
    if not result:
        sys.exit(1)
    else:
        print(f"Validated {assertion_str.title().replace('_', ' ')}")


def test_paths():
    locations = [
        '@enter(sw-1[GigabitEthernet0/0])',
        '@enter(sw-2[GigabitEthernet0/0])'
    ]
    for location in locations:
        path_result = asserts.assert_flows_succeed(
            startLocation=location,
            headers=HeaderConstraints(dstIps='8.8.8.8', srcIps='192.168.1.5'),
            snapshot="snapshot-1",
            session=bf_session
        )
        if not path_result:
            sys.exit(1)
        else:
            print(f"Test from {location} to DNS has passed!")


def test_custom_checks():
    """
    - Desktop pod has no routes to security servers.
    - Route to DNS must be a OSPF E2 route from Desktop pod.
    - All edge- devices must have a BGP session towards an ISP in Established state.
    """
    bf_routes = bf_session.q.routes().answer().frame()
    result = asserts.assert_has_no_route(routes=bf_routes, expected_route="192.168.123.0/24", node="sw-1")
    if not result:
        sys.exit(1)
    else:
        print("Desktop pod has no routes to security servers. passed!")
    dns_routes = bf_session.q.routes(nodes="/sw/", network="8.8.8.8/32").answer().frame()
    if not dns_routes.Protocol.all() == "ospfE2":
        sys.exit(1)
    else:
        print("Route to DNS must be a OSPF E2 route from Desktop pod. passed!")
    isp_neighbors = bf_session.q.bgpEdges(nodes="/edge/", remoteNodes="/isp/").answer().frame()
    isp_result = asserts.assert_num_results(isp_neighbors, 2)
    if not isp_result:
        sys.exit(1)
    else:
        print("There is always at least one BGP session towards an ISP in Established state. passed!")


if __name__ == "__main__":
    setup()
    assert_list = [
        "assert_no_unestablished_bgp_sessions",
        "assert_no_incompatible_bgp_sessions",
        "assert_no_incompatible_ospf_sessions"
    ]
    for assertion in assert_list:
        test_protocols(assertion)
    test_paths()
    test_custom_checks()

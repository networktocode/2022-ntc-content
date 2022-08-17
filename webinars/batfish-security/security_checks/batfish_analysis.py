"""Batfish Webinar 1."""
from datetime import date

from pybatfish.client.session import Session

SNAPSHOT_DIR = '../data/'


class BatfishWebinar:
    """Quick class to perform security cleanups."""

    def __init__(self, bf_host, bf_network, bf_snapshot):
        """Initializer."""
        self.bf_session = self._bf_setup(bf_host, bf_network, bf_snapshot)

    def _bf_setup(self, host, network, snapshot):
        """Simple Pybatfish Setup."""
        bf = Session(host=host)
        bf.set_network(network)
        bf.init_snapshot(SNAPSHOT_DIR, name=snapshot, overwrite=True)
        bf.set_snapshot(snapshot)
        return bf

    @staticmethod
    def _save_to_html(answer_df, filename):
        with open(f"../batfish_results/{filename}", "w") as file:
            file.write(f"<h1>Today's date: {date.today()}</h1>")
            file.write(answer_df.to_html())

    def _get_unused_structures(self):
        """Query Batfish to get Unused Structures."""
        return self._save_to_html(self.bf_session.q.unusedStructures().answer().frame(), filename="unused_structures.html")

    def _get_undefined_references(self):
        """Query Batfish for undefined references."""
        return self._save_to_html(self.bf_session.q.undefinedReferences().answer().frame(), filename="undefined_references.html")

    def _get_unreachable_lines(self):
        """Query Batfish for unreachable lines in ACLs/Policies."""
        return self._save_to_html(self.bf_session.q.filterLineReachability().answer().frame(), filename="unreachable_lines.html")

    def execute_bf_questions(self):
        """Execute Webinar Questions."""
        try:
            self._get_unused_structures()
            self._get_undefined_references()
            self._get_unreachable_lines()
            return "Successfully Queries Batfish."
        except Exception as err:
            return f"Error Occurred {err}"


if __name__ == "__main__":
    bw = BatfishWebinar("localhost", "security_network", "webinar1")
    result = bw.execute_bf_questions()
    print("=" * 20)
    print(result)
    print("=" * 20)

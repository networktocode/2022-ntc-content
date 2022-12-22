"""Test Panorama adapter."""

import json
import uuid
from unittest.mock import MagicMock

from django.contrib.contenttypes.models import ContentType
from nautobot.extras.models import Job, JobResult
from nautobot.utilities.testing import TransactionTestCase
from nautobot_ssot_panorama.diffsync.adapters.panorama import PanoramaAdapter
from nautobot_ssot_panorama.jobs import PanoramaDataSource


def load_json(path):
    """Load a json file."""
    with open(path, encoding="utf-8") as file:
        return json.loads(file.read())


SITE_FIXTURE = []


class TestPanoramaAdapterTestCase(TransactionTestCase):
    """Test NautobotSSoTPanoramaAdapter class."""

    databases = ("default", "job_logs")

    def setUp(self):
        """Initialize test case."""
        self.panorama_client = MagicMock()
        self.panorama_client.get_sites.return_value = SITE_FIXTURE

        self.job = PanoramaDataSource()
        self.job.job_result = JobResult.objects.create(
            name=self.job.class_path, obj_type=ContentType.objects.get_for_model(Job), user=None, job_id=uuid.uuid4()
        )
        self.panorama = PanoramaAdapter(job=self.job, sync=None, client=self.panorama_client)

    def test_data_loading(self):
        """Test Nautobot SSoT Panorama load() function."""
        # self.panorama.load()
        # self.assertEqual(
        #     {site["name"] for site in SITE_FIXTURE},
        #     {site.get_unique_id() for site in self.panorama.get_all("site")},
        # )

# Copyright 2015 Cloudbase Solutions Srl
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock

from nova.virt.hyperv.cluster import migrationops
from nova.tests.unit.virt.hyperv import test_base
from nova.virt.hyperv.cluster import clusterutils


class ClusterMigrationOpsTestCase(test_base.HyperVBaseTestCase):

    @mock.patch.object(clusterutils.ClusterUtils, '_init_hyperv_conn')
    def setUp(self, mock_hyperv_conn):
        super(ClusterMigrationOpsTestCase, self).setUp()
        self._clustmigrops = migrationops.ClusterMigrationOps()
        self._clustmigrops._clustutils = mock.Mock()
        self._clustmigrops._clustutils._conn = mock.MagicMock()

    def test_is_dest_same_host(self):
        get_clustnames = self._clustmigrops._clustutils.get_cluster_node_names
        fake_host = mock.sentinel.host
        get_clustnames.return_value = [fake_host]

        result = self._clustmigrops._is_dest_same_host(fake_host)

        self.assertTrue(result)

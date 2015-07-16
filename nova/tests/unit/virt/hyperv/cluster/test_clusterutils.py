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

from nova import exception
from nova.tests.unit.virt.hyperv import test_base
from nova.virt.hyperv.cluster import clusterutils
from nova.virt.hyperv import vmutils


class ClusterUtilsBaseTestCase(test_base.HyperVBaseTestCase):
    """Unit tests for the Hyper-V ClusterUtilsBase class."""

    @mock.patch.object(clusterutils.ClusterUtilsBase, '_init_hyperv_conn')
    def setUp(self, mock_hyperv_conn):
        super(ClusterUtilsBaseTestCase, self).setUp()
        self._clustutils = clusterutils.ClusterUtilsBase()
        self._clustutils._conn = mock.MagicMock()
        self._clustutils._cluster = mock.MagicMock()

    def test_get_cluster_nodes(self):
        result = self._clustutils._get_cluster_nodes()
        clust_assoc = self._clustutils._cluster.associators
        clust_assoc.assert_called_once_with(
            wmi_result_class=self._clustutils._MSCLUSTER_NODE)
        self.assertEqual(self._clustutils._cluster.associators.return_value,
                         result)

    def test_get_vm_groups(self):
        mock_res1 = mock.MagicMock()
        mock_res2 = mock.MagicMock(GroupType=mock.sentinel.bad_group_type)
        mock_res3 = mock.MagicMock(GroupType=self._clustutils._VM_GROUP_TYPE)

        self._clustutils._cluster.associators.return_value = [
            mock_res1, mock_res2, mock_res3]

        result = self._clustutils._get_vm_groups()

        self.assertEqual([mock_res3], list(result))


class ClusterUtilsTestCase(test_base.HyperVBaseTestCase):

    @mock.patch.object(clusterutils.ClusterUtils, '_init_hyperv_conn')
    def setUp(self, mock_init_conn):
        super(ClusterUtilsTestCase, self).setUp()
        self._clustutils = clusterutils.ClusterUtils()
        self._clustutils._conn = mock.MagicMock()

    @mock.patch.object(clusterutils.ClusterUtils, '_lookup_vm_group')
    def test_lookup_group_check_exception(self, mock_lookup_vm_group):
        mock_lookup_vm_group.return_value = None
        fake_name = mock.sentinel.name

        self.assertRaises(exception.NotFound,
                          self._clustutils._lookup_vm_group_check,
                          fake_name)

        self._clustutils._lookup_vm_group.assert_called_once_with(fake_name)

    @mock.patch.object(clusterutils.ClusterUtils, '_lookup_vm_group')
    def test_lookup_group_check_noexc(self, mock_lookup_vm_group):
        mock_lookup_vm_group.return_value = mock.sentinel.vm_group
        fake_name = mock.sentinel.name

        result = self._clustutils._lookup_vm_group_check(fake_name)

        self._clustutils._lookup_vm_group.assert_called_once_with(fake_name)
        self.assertEquals(mock_lookup_vm_group.return_value, result)

    @mock.patch.object(clusterutils.ClusterUtils, '_lookup_res')
    def test_lookup_vm_group(self, mock_lookup_res):
        mock_lookup_res.return_value = mock.sentinel.result
        fake_vm_name = mock.sentinel.vm_name

        result = self._clustutils._lookup_vm_group(fake_vm_name)

        self.assertEquals(result, mock_lookup_res.return_value)
        lookup_res = self._clustutils._lookup_res
        lookup_res.assert_called_once_with(
            self._clustutils._conn.MSCluster_ResourceGroup,
            fake_vm_name)

    @mock.patch.object(clusterutils.ClusterUtils, '_lookup_vm')
    def test_lookup_vm_check_exc(self, mock_lookup_vm):
        fake_name = mock.sentinel.name
        mock_lookup_vm.return_value = None

        self.assertRaises(exception.NotFound,
                          self._clustutils._lookup_vm_check,
                          fake_name)
        self._clustutils._lookup_vm.assert_called_once_with(fake_name)

    @mock.patch.object(clusterutils.ClusterUtils, '_lookup_vm')
    def test_lookup_vm_check_noexc(self, mock_lookup_vm):
        fake_name = mock.sentinel.name
        mock_lookup_vm.return_value = mock.sentinel.result

        result = self._clustutils._lookup_vm_check(fake_name)

        self.assertEquals(mock_lookup_vm.return_value, result)

    def _test_lookup_res(self, rsrc_count):
        mock_resource_src = mock.Mock()
        mock_resource_src.return_value = [mock.sentinel.resource] * rsrc_count
        fake_name = mock.sentinel.name

        if rsrc_count > 1:
            self.assertRaises(vmutils.HyperVException,
                              self._clustutils._lookup_res,
                              mock_resource_src,
                              fake_name)

        else:
            result = self._clustutils._lookup_res(mock_resource_src,
                                                  fake_name)
            if rsrc_count == 0:
                self.assertEquals(None, result)

            else:
                self.assertEquals(mock_resource_src.return_value[0],
                                  result)

        mock_resource_src.assert_called_once_with(Name=fake_name)

    def test_lookup_res_not_found(self):
        self._test_lookup_res(0)

    def test_lookup_res_multiple_found(self):
        self._test_lookup_res(5)

    def test_lookup_res_found(self):
        self._test_lookup_res(1)

    @mock.patch.object(clusterutils.ClusterUtils, '_get_cluster_nodes')
    def test_get_cluster_node_names(self, mock_get_cluster_nodes):
        fake_node_names = [mock.sentinel.node1, mock.sentinel.node2]
        mock_nodes = [mock.Mock(Name=node_name)
                      for node_name in fake_node_names]
        mock_get_cluster_nodes.return_value = mock_nodes

        result = self._clustutils.get_cluster_node_names()

        self.assertEquals(fake_node_names, result)

    @mock.patch.object(clusterutils.ClusterUtils, '_lookup_vm_group_check')
    def test_get_vm_host(self, mock_lookup_vm_group_check):
        fake_vm_name = 'fake name'
        mock_lookup_vm_group_check.return_value = mock.Mock()

        result = self._clustutils.get_vm_host(fake_vm_name)

        self.assertEquals(result,
                          mock_lookup_vm_group_check.return_value.OwnerNode)

    @mock.patch.object(clusterutils.ClusterUtils, '_lookup_vm_group_check')
    def test_add_vm_to_cluster(self, mock_lookup_vm_group_check):
        mock_vm_group = mock_lookup_vm_group_check.return_value
        fake_vm_name = mock.sentinel.name
        self._clustutils._cluster = mock.Mock()

        self._clustutils.add_vm_to_cluster(fake_vm_name)

        self._clustutils._cluster.AddVirtualMachine.assert_called_once_with(
            fake_vm_name)
        self.assertEquals(mock_vm_group.PersistentState, True)
        self.assertEquals(mock_vm_group.AutoFailbackType,
                          self._clustutils._FAILBACK_TRUE)
        self.assertEquals(mock_vm_group.FailbackWindowStart,
                          self._clustutils._FAILBACK_WINDOW_MIN)
        self.assertEquals(mock_vm_group.FailbackWindowEnd,
                          self._clustutils._FAILBACK_WINDOW_MAX)
        mock_vm_group.Put_.assert_called_once_with()

    @mock.patch.object(clusterutils.ClusterUtils, '_lookup_vm_group')
    def remove_vm_from_cluster(self, mock_lookup_vm_group):
        mock_vm_group = mock_lookup_vm_group()
        fake_vm_name = mock.sentinel.name

        self._clustutils.remove_vm_from_cluster(fake_vm_name)

        mock_vm_group.return_value.DestroyGroup.assert_called_once_with(
            self._clustutils._DESTROY_GROUP)

    @mock.patch.object(clusterutils.ClusterUtils, '_lookup_vm')
    def test_vm_exists(self, mock_lookup_vm):
        fake_vm_name = mock.sentinel.name
        mock_lookup_vm.return_value = mock.sentinel.vm_inst

        result = self._clustutils.vm_exists(fake_vm_name)

        mock_lookup_vm.assert_called_once_with(fake_vm_name)
        self.assertTrue(result)

    @mock.patch.object(clusterutils.ClusterUtils, '_migrate_vm')
    def test_live_migrate_vm(self, mock_migrate_vm):
        fake_vm_name = mock.sentinel.name
        fake_new_host = mock.sentinel.host

        self._clustutils.live_migrate_vm(fake_vm_name, fake_new_host)

        mock_migrate_vm.assert_called_once_with(
            fake_vm_name,
            fake_new_host,
            self._clustutils._LIVE_MIGRATION_TYPE)

    @mock.patch.object(clusterutils.ClusterUtils, '_lookup_vm_group_check')
    def test_migrate_vm(self, mock_lookup_group_check):
        fake_vm_group = mock_lookup_group_check.return_value

        fake_vm_group.MoveToNewNodeParams.side_effect = Exception
        self._clustutils._migrate_vm(mock.sentinel.vm_name, 
                                     mock.sentinel.new_host,
                                     mock.sentinel.migr_type)

        fake_vm_group.MoveToNewNodeParams.assert_called_once_with(
            self._clustutils._IGNORE_LOCKED, mock.sentinel.new_host,
            [mock.sentinel.migr_type])

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
        clust_assoc.assert_called_once_with(self._clustutils._MSCLUSTER_NODE)
        self.assertEqual(self._cluster.associators.return_value, result)

    def test_get_vm_groups(self):
        mock_res1 = mock.MagicMock()
        mock_res2 = mock.MagicMock(GroupType=mock.sentinel.bad_group_type)
        mock_res3 = mock.MagicMock(GroupType=self._clustutils._VM_GROUP_TYPE)

        self._clustutils._cluster.associators.return_value = [
            mock_res1, mock_res2, mock_res3]

        result = self._clustutils._get_vm_groups()

        self.assertEqual([mock_res3], list(result))


class ClusterUtilsTestCase(test_base.HyperVBaseTestCase):
    _FAKE_INSTANCE_NAME = 'fake_instance_name'

    @mock.patch.object(clusterutils.ClusterUtils, '_init_hyperv_conn')
    def setUp(self, mock_init_conn):
        super(ClusterUtilsTestCase, self).setUp()
        self._clustutils = clusterutils.ClusterUtils()
        self._clustutils._conn = mock.MagicMock()

    @mock.patch.object(clusterutils.ClusterUtils, '_lookup_vm_group')
    def test_lookup_group_check_exception(self, mock_lookup_vm_group):
        mock_lookup_vm_group.return_value = None
        fake_name = 'fake_name'

        self.assertRaises(exception.NotFound,
                          self._clustutils._lookup_vm_group_check,
                          fake_name)

        self._clustutils._lookup_vm_group.assert_called_once_with(fake_name)

    @mock.patch.object(clusterutils.ClusterUtils, '_lookup_vm_group')
    def test_lookup_group_check_noexc(self, mock_lookup_vm_group):
        mock_lookup_vm_group.return_value = 'fake_VM'
        fake_name = 'fake_name'

        result = self._clustutils._lookup_vm_group_check(fake_name)

        self._clustutils._lookup_vm_group.assert_called_once_with(fake_name)
        self.assertEquals(result, mock_lookup_vm_group.return_value)

    @mock.patch.object(clusterutils.ClusterUtils, '_lookup_res')
    def test_lookup_vm_group(self, mock_lookup_res):
        mock_lookup_res.return_value = 'fake result'
        fake_vm_name = 'fake_name'

        result = self._clustutils._lookup_vm_group(fake_vm_name)

        self.assertEquals(result, mock_lookup_res.return_value)
        lookup_res = self._clustutils._lookup_res
        lookup_res.assert_called_once_with(
            self._clustutils._conn.MSCluster_ResourceGroup,
            fake_vm_name)

    @mock.patch.object(clusterutils.ClusterUtils, '_lookup_vm')
    def test_lookup_vm_check_exc(self, mock_lookup_vm):
        fake_name = 'fake name'
        mock_lookup_vm.return_value = None

        self.assertRaises(exception.NotFound,
                          self._clustutils._lookup_vm_check,
                          fake_name)
        self._clustutils._lookup_vm.assert_called_once_with(fake_name)

    @mock.patch.object(clusterutils.ClusterUtils, '_lookup_vm')
    def test_lookup_vm_check_noexc(self, mock_lookup_vm):
        fake_name = 'fake name'
        mock_lookup_vm.return_value = 'fake vm'

        result = self._clustutils._lookup_vm_check(fake_name)

        self.assertEquals(result, mock_lookup_vm.return_value)

    def _test_lookup_res(self, rsrc_count):
        mock_resource_src = mock.Mock()
        mock_resource_src.return_value = [mock.sentinel.resource] * rsrc_count
        fake_name = 'fake name'

        if rsrc_count == 0:
            result = self._clustutils._lookup_res(mock_resource_src,
                                                  fake_name)
            self.assertEquals(None, result)

        elif rsrc_count > 1:
            self.assertRaises(vmutils.HyperVException,
                              self._clustutils._lookup_res,
                              mock_resource_src,
                              fake_name)

        else:
            result = self._clustutils._lookup_res(mock_resource_src,
                                                  fake_name)
            self.assertEquals(mock_resource_src.return_value[0],
                              result)
        mock_resource_src.assert_called_once_with(Name=fake_name)

    def test_lookup_res_none(self):
        self._test_lookup_res(0)

    def test_lookup_res_many(self):
        self._test_lookup_res(5)

    def test_lookup_res_one(self):
        self._test_lookup_res(1)

    @mock.patch.object(clusterutils.ClusterUtils, 'get_cluster_node_names')
    def test_get_cluster_node_names(self, mock_get_cluster_nodes):
        res1 = mock.Mock()
        res2 = mock.Mock()
        fake_nodes = [res1, res2]
        expected_result = [res1.Name, res2.Name]
        mock_get_cluster_nodes.return_value = fake_nodes

        result = self._clustutils.get_cluster_node_names()

        self.assertEquals(expected_result, result)

    @mock.patch.object(clusterutils.ClusterUtils, '_lookup_vm_group_check')
    def test_get_vm_host(self, mock_lookup_vm_group_check):
        fake_vm_name = 'fake name'
        mock_lookup_vm_group_check.return_value = mock.Mock()

        result = self._clustutils.get_vm_host(fake_vm_name)

        self.assertEquals(result,
                          mock_lookup_vm_group_check.return_value.OwnerNode)

    @mock.patch.object(clusterutils.ClusterUtils, '_lookup_vm_group_check')
    def test_add_vm_to_cluster(self, mock_lookup_vm_group_check):
        mock_lookup_vm_group_check.return_value = mock.Mock()
        mock_vm = mock_lookup_vm_group_check()
        fake_vm_name = 'fake vm name'
        self._clustutils._cluster = mock.Mock()

        self._clustutils.add_vm_to_cluster(fake_vm_name)

        self._clustutils._cluster.AddVirtualMachine.assert_called_once_with(
            fake_vm_name)
        self.assertEquals(mock_vm.PersistentState, True)
        # If the function doesn't return something how do I check the fields?

    @mock.patch.object(clusterutils.ClusterUtils, '_lookup_vm_group')
    def remove_vm_from_cluster(self, mock_lookup_vm_group):
        mock_lookup_vm_group.return_value = mock.Mock()
        mock_vm = mock_lookup_vm_group()
        fake_vm_name = 'fake vm name'

        self._clustutils.remove_vm_from_cluster(fake_vm_name)

        mock_vm.return_value.DestroyGroup.assert_called_once_with(
            self._clustutils._DESTROY_GROUP)

    @mock.patch.object(clusterutils.ClusterUtils, '_lookup_vm')
    def test_vm_exists(self, mock_lookup_vm):
        fake_vm_name = 'fake name'

        self._clustutils.vm_exists(fake_vm_name)

        mock_lookup_vm.assert_called_once_with(fake_vm_name)

    def test_live_migrate_vm(self):
        fake_vm_name = 'fake_name'
        fake_new_host = 'fake host'

        self._clustutils.live_migrate_vm(fake_vm_name, fake_new_host)

        self._clustutils._migrate_vm.assert_called_once_with(
            fake_vm_name,
            fake_new_host,
            self._clustutils._LIVE_MIGRATION_TYPE)

    @mock.patch.object(clusterutils.ClusterUtils, '_lookup_vm_group_check')
    def test_migrate_vm(self, mock_lookup_group_check):
        fake_new_host = 'fake host'
        fake_migr_type = 'fake type'
        mock_lookup_group_check.return_value = mock.Mock()
        fake_vm = mock_lookup_group_check.return_value

        self.assertRaises(Exception,
                          fake_vm.MoveToNewNodeParams,
                          self._clustutils._IGNORE_LOCKED,
                          fake_new_host,
                          [fake_migr_type])

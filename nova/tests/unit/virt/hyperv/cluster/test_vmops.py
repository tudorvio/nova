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

from nova.tests.unit.virt.hyperv import test_base
from nova.virt.hyperv.cluster import vmops
from nova.tests.unit import fake_instance
from nova.virt.hyperv.cluster import clusterutils


class ClusterVMOpsTestCase(test_base.HyperVBaseTestCase):

    @mock.patch.object(clusterutils.ClusterUtils, '_init_hyperv_conn')
    def setUp(self, mock_hyperv_conn):
        super(ClusterVMOpsTestCase, self).setUp()
        self._cluster_vmops = vmops.ClusterVMOps()
        self._cluster_vmops._clustutils = mock.Mock()
        self._cluster_vmops._clustutils._conn = mock.MagicMock()
        self.mock_instance = fake_instance.fake_instance_obj('fake context')

    @mock.patch('nova.virt.hyperv.vmops.VMOps.create_instance')
    def test_create_instance(self, mock_parent_create_inst):
        fake_netinfo = 'fake netinfo'
        fake_block_info = 'fake block info'
        fake_root_vhd_path = 'fake vhd info'
        fake_eph_vhd_path = 'fake eph vhd path'
        fake_vm_gen = 'fake vm gen'

        self._cluster_vmops.create_instance(instance=self.mock_instance,
                                            network_info=fake_netinfo,
                                            block_device_info=fake_block_info,
                                            root_vhd_path=fake_root_vhd_path,
                                            eph_vhd_path=fake_eph_vhd_path,
                                            vm_gen=fake_vm_gen)

        mock_parent_create_inst.assert_called_once_with(self.mock_instance,
                                                        fake_netinfo,
                                                        fake_block_info,
                                                        fake_root_vhd_path,
                                                        fake_eph_vhd_path,
                                                        fake_vm_gen)

        add_vm_to_cluster = self._cluster_vmops._clustutils.add_vm_to_cluster
        add_vm_to_cluster.assert_called_once_with(self.mock_instance.name)

    @mock.patch('nova.virt.hyperv.vmops.VMOps.destroy')
    def test_destroy(self, mock_parent_destroy):
        self._cluster_vmops.destroy(self.mock_instance)

        remove_vm = self._cluster_vmops._clustutils.remove_vm_from_cluster
        remove_vm.assert_called_once_with(self.mock_instance)
        mock_parent_destroy.assert_called_once_with(self.mock_instance, None,
                                                    None, True)

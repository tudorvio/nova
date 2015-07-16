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
        self._mock_instance = fake_instance.fake_instance_obj(
            mock.sentinel.context)

    @mock.patch('nova.virt.hyperv.vmops.VMOps.create_instance')
    def test_create_instance(self, mock_parent_create_inst):
        fake_netinfo = mock.sentinel.netinfo
        fake_block_info = mock.sentinel.block_info
        fake_root_vhd_path = mock.sentinel.root_vhd_path
        fake_eph_vhd_path = mock.sentinel.eph_vhd_path
        fake_vm_gen = mock.sentinel.vm_gen

        self._cluster_vmops.create_instance(instance=self._mock_instance,
                                            network_info=fake_netinfo,
                                            block_device_info=fake_block_info,
                                            root_vhd_path=fake_root_vhd_path,
                                            eph_vhd_path=fake_eph_vhd_path,
                                            vm_gen=fake_vm_gen)

        mock_parent_create_inst.assert_called_once_with(self._mock_instance,
                                                        fake_netinfo,
                                                        fake_block_info,
                                                        fake_root_vhd_path,
                                                        fake_eph_vhd_path,
                                                        fake_vm_gen)

        add_vm_to_cluster = self._cluster_vmops._clustutils.add_vm_to_cluster
        add_vm_to_cluster.assert_called_once_with(self._mock_instance.name)

    @mock.patch('nova.virt.hyperv.vmops.VMOps.destroy')
    def test_destroy(self, mock_parent_destroy):
        fake_netinfo = mock.sentinel.netinfo
        fake_block_device = mock.sentinel.block_device
        fake_destroy_disks = mock.sentinel.destr_disks

        self._cluster_vmops.destroy(instance=self._mock_instance,
                                    network_info=fake_netinfo,
                                    block_device_info=fake_block_device,
                                    destroy_disks=fake_destroy_disks)

        remove_vm = self._cluster_vmops._clustutils.remove_vm_from_cluster
        remove_vm.assert_called_once_with(self._mock_instance.name)
        mock_parent_destroy.assert_called_once_with(self._mock_instance,
                                                    fake_netinfo,
                                                    fake_block_device,
                                                    fake_destroy_disks)

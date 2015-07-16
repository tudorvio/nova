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

"""
Management class for basic clustered VM operations.
"""

from oslo_log import log as logging

from nova.i18n import _LI
from nova.virt.hyperv.cluster import clusterutils
from nova.virt.hyperv import vmops

LOG = logging.getLogger(__name__)


class ClusterVMOps(vmops.VMOps):

    def __init__(self):
        super(ClusterVMOps, self).__init__()
        self._clustutils = clusterutils.ClusterUtils()

    def create_instance(self, instance, network_info, block_device_info,
                        root_vhd_path, eph_vhd_path, vm_gen):
        super(ClusterVMOps, self).create_instance(
            instance, network_info, block_device_info, root_vhd_path,
            eph_vhd_path, vm_gen)
        LOG.info(_LI('Clustering instance...'), instance=instance)
        self._clustutils.add_vm_to_cluster(instance.name)

    def destroy(self, instance, network_info=None, block_device_info=None,
                destroy_disks=True):
        LOG.info(_LI('Unclustering instance...'), instance=instance)
        self._clustutils.remove_vm_from_cluster(instance.name)
        super(ClusterVMOps, self).destroy(instance, network_info,
                                          block_device_info, destroy_disks)

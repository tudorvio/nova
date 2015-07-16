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
Management class for Cluster migration / resize operations.
"""

from nova.virt.hyperv.cluster import clusterutils
from nova.virt.hyperv.cluster import vmops
from nova.virt.hyperv import migrationops


class ClusterMigrationOps(migrationops.MigrationOps):

    def __init__(self):
        super(ClusterMigrationOps, self).__init__()
        self._vmops = vmops.ClusterVMOps()
        self._clustutils = clusterutils.ClusterUtils()

    def _is_dest_same_host(self, host):
        # check if the destination is in the same cluster.
        # if it is, the disks are in the same shared storage.
        return host in self._clustutils.get_cluster_node_names()

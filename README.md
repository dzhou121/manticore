Manticore enables Openstack Neutron networking component to be able to advise
BGP routing information for floating IPs to a BGP router.

After installtion, it will create two binary files:

manticore-bgp-speaker
manticore-l3-agent

manticore-bgp-speaker can be running on a BGP speaker node, which will
subscribe to Openstack messaging bus and do BGP updates.

manticore-l3-agent is a modification of Neutron's original L3 agent to allow it
to notify the BGP speaker whenever there is a floating IP update.

package manticore.l3_router_plugin.ManticoreL3RouterPlugin needs to be put in
Neutron's main API node's service plugins configuration

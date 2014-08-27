import socket

from oslo.config import cfg
from manticore import rpc

core_opts = [
    cfg.StrOpt('host', default=socket.gethostname(),
               help=("The hostname of this node")),
]

bgp_opts = [
    cfg.IntOpt('as_number', default=65000,
               help=("The AS number of this BGP Speaker")),
    cfg.StrOpt('router_id', default='192.168.1.231',
               help=("The router id of this BGP Speaker")),
    cfg.IntOpt('neighbor_as_number', default=65000,
               help=("The AS number of BGP neighbor")),
    cfg.StrOpt('neighbor_router_id', default='192.168.1.232',
               help=("The router id of BGP neighbor")),
]

cfg.CONF.register_opts(core_opts)
cfg.CONF.register_opts(bgp_opts, 'BGP')


def init(args, **kwargs):
    rpc.set_defaults(control_exchange='neutron')
    cfg.CONF(args=args, project='manticore',
             version='0.1',
             **kwargs)
    rpc.init(cfg.CONF)

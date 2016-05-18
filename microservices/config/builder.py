import multiprocessing

from oslo_config import cfg


CONF = cfg.CONF
builder_opts = [
    cfg.IntOpt('workers',
               default=multiprocessing.cpu_count(),
               help='Number of workers which build docker images'),
    cfg.BoolOpt('push',
                default=False,
                help='Push to the Docker registry'),
    cfg.StrOpt('registry',
               default='127.0.0.1:5000',
               help='Docker registry address (host:port)'),
    cfg.BoolOpt('insecure-registry',
                default=False,
                help='Permit to push without SSL')
]
builder_opt_group = cfg.OptGroup(name='builder',
                                 title='Images builder')
CONF.register_group(builder_opt_group)
CONF.register_cli_opts(builder_opts, builder_opt_group)
CONF.register_opts(builder_opts, builder_opt_group)
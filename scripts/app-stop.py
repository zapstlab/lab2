from cloudify import ctx

ctx.logger.info('---> VNF APP {} is stopping...'.format(str(ctx.node.name)))

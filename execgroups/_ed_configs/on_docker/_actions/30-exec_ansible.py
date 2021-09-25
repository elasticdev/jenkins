def default():
    
    task = {}
    env_vars = []
    shelloutconfigs = []

    env_vars.append('elasticdev:::ansible::create')
    shelloutconfigs.append('elasticdev:::ansible::resource_wrapper')

    task['method'] = 'shelloutconfig'
    task['metadata'] = {'env_vars': env_vars,
                        'shelloutconfigs': shelloutconfigs
                        }

    return task


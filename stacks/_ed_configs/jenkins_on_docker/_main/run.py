def _get_instance_info(stack,hostname):

    _lookup = {"must_exists":True}
    _lookup["must_be_one"] = True
    _lookup["resource_type"] = "server"
    _lookup["hostname"] = hostname

    return list(stack.get_resource(**_lookup))[0]

def _get_ssh_key(stack):

    _lookup = {"must_exists":True}
    _lookup["resource_type"] = "ssh_key_pair"
    _lookup["name"] = stack.ssh_key_name
    _lookup["serialize"] = True
    _lookup["serialize_keys"] = [ "private_key" ]

    return stack.get_resource(decrypt=True,**_lookup)["private_key"]

def run(stackargs):

    import json

    # instantiate authoring stack
    stack = newStack(stackargs)

    # Add default variables
    stack.parse.add_required(key="hostname")
    stack.parse.add_required(key="ssh_key_name")
    stack.parse.add_optional(key="vm_username",default="root")

    stack.parse.add_optional(key="publish_creds",default=True,null_allowed=True)
    stack.parse.add_optional(key="ansible_docker_exec_env",default="elasticdev/ansible-run-env")

    # Add execgroup
    stack.add_execgroup("elasticdev:::jenkins::on_docker")

    # Initialize 
    stack.init_variables()
    stack.init_execgroups()

    instance_info = _get_instance_info(stack,stack.hostname)
    public_ip = instance_info["public_ip"]

    # get ssh_key
    private_key = _get_ssh_key(stack)
    stateful_id = stack.random_id(size=10)

    env_vars = {"METHOD":"create"}
    env_vars["docker_exec_env".upper()] = stack.ansible_docker_exec_env
    env_vars["ANSIBLE_DIR"] = "/var/tmp/ansible"
    env_vars["STATEFUL_ID"] = stateful_id
    _hosts = { "all":[public_ip] }

    stack.logger.debug("z1"*32)
    stack.logger.debug("")
    stack.logger.debug(_hosts)
    stack.logger.debug("")
    stack.logger.debug("z2"*32)
    stack.logger.debug("")
    stack.logger.debug(json.dumps(_hosts))
    stack.logger.debug("")
    stack.logger.debug("z3"*32)

    env_vars["ANS_VAR_hosts"] = stack.b64_encode(json.dumps(_hosts))
    stack.logger.debug("z4"*32)

    env_vars["ANS_VAR_private_key_hash"] = stack.b64_encode(private_key)
    stack.logger.debug("z5"*32)

    inputargs = {"display":True}
    inputargs["human_description"] = 'Install Jenkins for Ansible'
    inputargs["env_vars"] = json.dumps(env_vars.copy())
    inputargs["stateful_id"] = stateful_id
    inputargs["automation_phase"] = "infrastructure"
    inputargs["hostname"] = stack.hostname
    inputargs["groups"] = stack.on_docker

    stack.add_groups_to_host(**inputargs)

    # publish variables
    _publish_vars = {"hostname":stack.hostname}
    _publish_vars["public_ip"] = public_ip

    stack.publish(_publish_vars)

    return stack.get_results()

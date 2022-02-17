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

    return stack.get_resource(decrypt=True,**_lookup)[0]["private_key"]

def run(stackargs):

    import json

    # instantiate authoring stack
    stack = newStack(stackargs)

    # Add default variables
    stack.parse.add_required(key="hostname")
    stack.parse.add_required(key="ssh_key_name")
    stack.parse.add_required(key="publish_private_key",default="null")
    stack.parse.add_optional(key="ansible_docker_exec_env",default="elasticdev/ansible-run-env")

    # Add execgroup
    stack.add_execgroup("elasticdev:::jenkins::on_docker")
    stack.add_substack('elasticdev:::ed_core::publish_host_file')

    # Initialize 
    stack.init_variables()
    stack.init_execgroups()
    stack.init_substacks()

    instance_info = _get_instance_info(stack,stack.hostname)
    public_ip = instance_info["public_ip"]

    # get ssh_key and convert to base64 string
    _private_key_hash = stack.b64_encode(_get_ssh_key(stack))

    # generate stateful id
    stateful_id = stack.random_id(size=10)

    env_vars = {"STATEFUL_ID":stateful_id}
    env_vars["docker_exec_env".upper()] = stack.ansible_docker_exec_env
    env_vars["ANSIBLE_DIR"] = "var/tmp/ansible"
    env_vars["ANS_VAR_private_key_hash"] = _private_key_hash

    _hosts = { "all":[public_ip] }
    env_vars["ANS_VAR_hosts"] = stack.b64_encode(json.dumps(_hosts))
    env_vars["ANS_VAR_exec_ymls"] = "install.yml"
    env_vars["ANSIBLE_EXEC_YMLS"] = "install.yml"

    inputargs = {"display":True}
    inputargs["human_description"] = 'Install Jenkins for Ansible'
    inputargs["env_vars"] = json.dumps(env_vars.copy())
    inputargs["stateful_id"] = stateful_id
    inputargs["automation_phase"] = "infrastructure"
    inputargs["hostname"] = stack.hostname
    stack.on_docker.insert(**inputargs)

    # publish variables
    _publish_vars = {"hostname":stack.hostname}
    _publish_vars["public_ip"] = public_ip

    if stack.publish_private_key:
        _publish_vars["private_key_hash"] = _private_key_hash

    stack.publish(_publish_vars)

    # fetch and publish jenkins admin password
    default_values = { "hostname":stack.hostname }
    default_values["ssh_key_name"] = stack.ssh_key_name

    overide_values = { "remote_file": "/var/lib/jenkins/secrets/initialAdminPassword" }
    overide_values["key"] = "init_password"

    inputargs = {"default_values":default_values,
                 "overide_values":overide_values}

    inputargs["automation_phase"] = "infrastructure"
    inputargs["human_description"] = 'Publish jenkins admin init password'
    stack.publish_host_file.insert(display=True,**inputargs)

    return stack.get_results()

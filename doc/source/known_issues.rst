.. _known_issues:

=====================
Services Known Issues
=====================

This sections describe known issues and corresponding workarounds, if they are.

[Heat] WaitCondition and SoftwareDeployment resources
=====================================================

Problem description
-------------------

CCP deploys Heat services with default configuration and changes endpoint_type
from publicURL to internalURL. However such configuration in Kubernetes cluster
is not enough for several type of resources like OS::Heat::Waitcondition and
OS::Heat::SoftwareDeployment, which require callback to Heat API or
Heat API CFN. Due to Kubernetes architecture it's not possible to do such
callback on the default port value (for heat-api it's - 8004 and 8000 for
heat-api-cfn). Note, that exactly these ports are used in endpoints registred
in keystone.

Also there is an issue with service domain name to ip resolving from VM booted
in Openstack.

There are two ways to fix these issues, which will be described below:
 - Out of the box, which requires just adding some data to ``.ccp.yaml``.
 - With manual actions.

Prerequisites for workarounds
-----------------------------

Before applying workaround please make sure, that current ccp deployment
satisfies the following prerequisites:
 - VM booted in Openstack can be reached via ssh (don't forget to configure
   corresponding security group rules).
 - IP address of Kubernetes node, where heat-api service is run, is accessible
   from VM booted in Openstack.

Workaround out of the box
-------------------------

This workaround is similar for both resources and it's related to kubernetes
node external ip usage node with hardcoded node port in config.

#. Add the following lines in the config ``.ccp.yaml``:

   ::

     k8s_external_ip: x.x.x.x
     heat:
       heat_endpoint_type: publicURL
       api_port:
         node: 31777
       api_cfn_port:
         node: 31778

   Where ``x.x.x.x`` is IP of kubernetes node, where Heat services are run.
   The second line explicitly sets publicURL in Heat config for initialisation
   of the heat client with public endpoint.
   Next lines set hardcoded ports for services: heat-api and heat-api-cfn. User
   may choose any free port from K8S range for these services.

   All these options should be used together, because external ip will be used
   by ccp only with node ports. Also combination of IP and port will be applied
   only for public enpoint.

#. After this change you may run ``ccp deploy`` command.

.. WARNING:: There are two potential risks here:

 - Specified node port is in use by some other service, so user needs to change
   another free port.
 - Using heatclient with enabled ingress can be broken. It was not tested fully
   yet.

Workaround after deploy
-----------------------

This workaround can be used, when Openstack is already deployed and cloud
administrator can change only one component.

#. Need to gather information about Node Ports and IP of Kubernetes node with
   services. User may get ``Node Ports`` for all heat API services by using
   the following commands:

   ::

     # get Node Port API
     kubectl get service heat-api -o yaml | awk '/nodePort: / {print $NF}'

     # get Node Port API CFN
     kubectl get service heat-api-cfn -o yaml | awk '/nodePort: / {print $NF}'

   Obtain ``service IP`` by executing ``ping`` command from Kubernetes host to
   domain names of services (e.g. ``heat-api.ccp``).

#. Then these IP and Node ports should be used as internal endpoints for
   corresponding services in keystone, i.e. replace old internal endpoints with
   domain names to IP with Node Ports for heat-api and heat-api-cfn. It should
   look like:

  ::

    # delete old endpoint
    openstack endpoint delete <id of internal endpoints>

    # create new endpoint for heat-api
    openstack endpoint create --region RegionOne \
    orchestration internal http://<service IP>:<Node Port API>/v1/%\(tenant_id\)s

    # create new endpoint for heat-api-cfn
    openstack endpoint create --region RegionOne \
    cloudformation internal http://<service IP>:<Node Port API CFN>/v1/

.. NOTE:: For Waitcondition resource validation simple `heat template`_ can be
          used.

#. The previous steps should be enough for fixing Waitcondition resource.
   However for SoftwareDeployment usage it is necessary to remove two options
   from ``fuel-ccp-heat/service/files/heat.conf.j2 file``:
     - heat_waitcondition_server_url
     - heat_metadata_server_url

   It's necessary, because otherwise they will be used instead of internal
   endpoints. Such change requires partial redeploy, which can be done with
   commands:

  ::

    ccp deploy -c heat-engine heat-api heat-api-cfn

To validate, that this change was applied just check, that new containers for
these services were started.

.. _heat template: https://github.com/openstack/heat-templates/blob/master/hot/native_waitcondition.yaml


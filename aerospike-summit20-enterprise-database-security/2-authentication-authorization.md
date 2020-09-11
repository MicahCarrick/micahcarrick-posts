In the **Enterprise Database Security** session I presented at [Aerospike Summit 2020](https://www.aerospike.com/summit/) I gave an overview of authentication and authorization with Aerospike Enterprise.

_[Download presentation PDF](https://cdn.carrick.tech/micahcarrick-posts/aerospike-summit20-enterprise-database-security/Aerospike%20Summit%202020%20-%20Enterprise%20Database%20Security.pdf)_

***

To provide context, refer to the following diagram depicting an Aerospike deployment.

![Aerospike Deployment Diagram](https://cdn.carrick.tech/micahcarrick-posts/aerospike-summit20-enterprise-database-security/aerospike-auth-deployment.png)

On the left we have developers building applications and back office jobs that will use an Aerospike database.

In the middle we have an Aerospike cluster managed by one or more administrative groups such as SREs, DevOps, DBAs, etc.

And on the right we have downstream systems which ingest and analyze security events and log data for use by information security teams.

The red group icons depict actors that need to interact with the Aerospike database in some way. How do we control who and what can access this data and how do we manage that within an existing enterprise architecture?

Identity and Access Management is a huge part of any enterprise IT organization. Aerospike includes a framework for authentication and authorization out-of-the-box, but it also integrates into your existing IAM infrastructure.


## Authentication (AuthN)

Both humans users _and_ machines (applications) need to authenticate when connecting to Aerospike Enterprise.

![Aerospike Internal Authentication](https://cdn.carrick.tech/micahcarrick-posts/aerospike-summit20-enterprise-database-security/aerospike-auth-internal-authn.png)

You may be pretty familiar with the concept of a human user having to authenticate with a database. You know, it’s like `GRANT some_permission to USER 'micah' on some_resource`. But let’s touch on _applications_ needing to authenticate.

As discussed as part of _Aerospike Network Security_, the nodes the applications are running on have been authenticated with TLS. But that was about network security. Is _this server_ allowed to communicate with _that server_.

Now we want to authenticate the _application_ running on that network so that we can later control what the application is authorized to do. In other words, we’re not trying to determine whether that application is allowed to communicate, we’re trying to determine _which_ application is communicating so we can later control what it is allowed to do. And to do that, we need that application to be authenticated--to identify itself.

Right out of the box you can enable Aerospike’s internal authentication, which is shown above. Both humans and applications present a username and password combination when connecting to Aerospike and all the user management is done directly within Aerospike.

This works for simple use cases and it’s a no-brainer to setup. However, every organization has their own unique set of IAM requirements. Things like password policies, credential lifecycle management, MFA, etc. The nuances and complexity of such systems is best delegated to the purpose-built tools already established in the enterprise IT infrastructure. So Aerospike supports integrating into these systems through _external authentication_.

![Aerospike External Authentication](https://cdn.carrick.tech/micahcarrick-posts/aerospike-summit20-enterprise-database-security/aerospike-auth-external-authn.png)

In the external authentication setup, Aerospike will delegate the credential check to the 3rd party system. In this case we’re looking at a typical directory to which Aerospike is integrated via LDAP. After a successful authentication, Aerospike will use an access token to authenticate subsequent connections for the lifetime of that token and then go back to the LDAP server as needed to re-authenticate.

This is a very common setup for human users of the database and in some cases applications as well.

However, with this architecture, the directory is in the critical path for the functionality of the applications using Aerospike. The LDAP directory may not be designed with the same availability, performance, or scale that an application is being designed for, so it may not be viable for all use cases.

![Aerospike Mixed Authentication](https://cdn.carrick.tech/micahcarrick-posts/aerospike-summit20-enterprise-database-security/aerospike-auth-mixed-authn.png)

So now we can look at an pattern that combines both authentication methods. LDAP and the directory are still used for humans to authenticate, but the applications authenticate using the internal system. Now this removes the LDAP directory from the critical path, however, it presents a different problem. Part of the role of the directory in the external authentication setup was centralizing IAM.

If users are managed directly in Aerospike, how are the credentials going to be provisioned, rotated, and revoked for the applications? How will the organization's policies and regulatory requirements be enforced?

In smaller organizations or autonomous business units, this may not pose a large problem. But in larger enterprises this becomes untenable.

This is where secrets management and dynamic credentials can help. Rather than the applications themselves having credentials to Aerospike, the applications query the secrets management system to obtain the credentials--often short lived credentials to lower risk.

The secrets management system has the access necessary to manage the full lifecycle of Aerospike credentials and does so within the domain of the existing centralized IAM.

With one of these three patterns we’ll have established which user or application is trying to do something, and can now authorize them or it to do so.

## Authorization (AuthZ)

We can apply access controls to the human users or applications by assigning them to Aerospike **roles**.

The role can then be allowed a set of **privileges**. A privilege consists of a permission to perform some action along with a scope. For example, the permission to read data at a global scope would be one privilege and the permission to read data only for a specific _set_ in a specific _namespace_ would be a different privilege.

This will allow for a least privileged access model in which any database user, be it a human user or application code, can be associated to roles that allow only the access necessary to perform their function.

![Aerospike Authorization](https://cdn.carrick.tech/micahcarrick-posts/aerospike-summit20-enterprise-database-security/aerospike-auth-authorization.png)

Let’s look at these examples using a hypothetical setup for Acme corp.

First, the **Acme IAM** role is for the administrative user or system, such as the secrets management system depicted in the previous slide, with a privilege to manage the full lifecycle of Aerospike users globally.

Next, the **Acme SRE** role in this example allows site reliability engineers to perform functions to address issues relating to system stability like querying server metrics, gracefully removing a node for maintenance, enabling different log levels, etc.

Next the **Acme DBA** role in this example allows database administrators to perform functions to optimize for the specific database use cases like managing secondary indexes, throttling scans, adding/removing user-defined functions, etc.

The final 3 roles in this example, **Acme App1**, **Acme App2**, and **Acme Daily Loader**, each allow the applications specific access to data, but scoped down to only that which is necessary for the function that application performs. For example, notice that the **Acme App2** role can only read data from the set named `app2` within the namespace `ns1`. It will not be allowed to read data from the set that **Acme App1** uses nor will it be able to write any data at all.

So this is how you can set up some fine-grained role-based access control for users and applications.

And finally, every role can be assigned a whitelist of IP CIDR ranges from which database users associated with that role can connect from. This provides an even finer level of granularity on top of the existing network security.

For example, maybe a handful employees can all connect to Aerospike from their workstations within a particular private subnet, but only Alice and Bob can create new users and only when they do so from their specific personal workstations.

## Further Reading

* [Aerospike - Configuring Access Control](https://www.aerospike.com/docs/operations/configure/security/access-control/index.html)
* [Aerospike - Configuring LDAP](https://www.aerospike.com/docs/operations/configure/security/ldap/index.html)

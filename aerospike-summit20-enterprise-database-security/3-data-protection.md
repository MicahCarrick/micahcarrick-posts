In the **Enterprise Database Security** session I presented at [Aerospike Summit 2020](https://www.aerospike.com/summit/) I gave an overview of data protection with Aerospike Enterprise.

_[Download presentation PDF](https://cdn.carrick.tech/micahcarrick-posts/aerospike-summit20-enterprise-database-security/Aerospike%20Summit%202020%20-%20Enterprise%20Database%20Security.pdf)_

***

To provide context, refer to the following diagram depicting an Aerospike deployment.

![Aerospike Deployment Diagram](https://cdn.carrick.tech/micahcarrick-posts/aerospike-summit20-enterprise-database-security/aerospike-data-protection-deployment.png)

Even after securing the network and implementing authentication and authorization, remember that we're persisting this data on physical devices somewhere. Even in the cloud there’s still racks and servers behind all that "magic".

So how do we protect that persisted data from unauthorized access and how do we reduce the attack surface?

***

## Data Isolation and Encryption

For protecting data at rest, that is, data persisted in the storage layer, we want to look at how we do data isolation and encryption in Aerospike.

![Aerospike Encryption at Rest](https://cdn.carrick.tech/micahcarrick-posts/aerospike-summit20-enterprise-database-security/aerospike-data-protection-encryption-at-rest.png)

The diagram above depicts two SSD devices physically attached to an Aerospike server node. These are _physical devices_.

In this example, each SSD device is also divided into two logical partitions for a total of 4 partitions. These are _logical devices_ and data stored on one partition is logically separate from data in the other partitions.

One of the authorization scopes we can apply to a permission with [Aerospike’s access controls](https://www.aerospike.com/docs/operations/configure/security/access-control/index.html) is `namespace`. Namespaces not only provide scope for access controls, they also configure the storage layer. That configuration includes which physical or logical devices the data is persisted to, enabling AES encryption, and which key is used to encrypt and decrypt that data.

So what that means is, from a data protection standpoint, each namespace provides data isolation from other namespaces. If the user credentials or the encryption key for Namespace #1 were to be compromised, the data stored in Namespace #2 is protected separately.


## OS Hardening and System Access Controls

The data is encrypted in transit with TLS and encrypted at rest using AES encryption on the namespace. So far so good.

However, the Aerospike process itself is obviously working with the unencrypted data in memory. Standard [OS/system hardening](https://en.wikipedia.org/wiki/Hardening_%28computing%29) procedures and system access controls are absolutely critical for Aerospike deployments that store sensitive data. I’m not going to get into Linux system hardening as it’s tangential and there are plenty of industry standard tools, processes, and requirements on that front. But I do want to emphasise a best practice:

**_Keep Aerospike nodes as singular in purpose._**

In general we don’t recommend running Aerospike along side any other non-related applications, but it’s especially important when working with sensitive data. It may be tempting or convenient to run some tools or dashboards directly on one of the Aerospike nodes but, that just increases the surface area for potential vulnerabilities. 

The tools or dashboards should not have direct access to sensitive data and therefore should not be running on an Aerospike node.

A less obvious example of this is the [Aerospike Tools](https://www.aerospike.com/docs/tools/) package which includes the `aql`, `asinfo` and `asadm` commands among others. These administrative tools are bundled with the Aerospike Server and they are required to be run directly on the Aerospike nodes for a subset of operational tasks. Obtaining a collectinfo is a good example of this.

However, the tools are also available as a stand-alone package and can be run from a remote server for most tasks. So a best practice is to make the Aerospike Tools available to authorized users on dedicated nodes specifically for that purpose. You will still want an escalation path that allows for node-level diagnostics and troubleshooting, however, that should be the exception and not the rule.

## Secrets Management

Protecting secrets in general is a very broad topic. So to keep things brief here I just want to enumerate the secrets associated with Aerospike that need to be protected and a couple of common patterns for how that’s done in a Production environment.

![Aerospike Secrets Management](https://cdn.carrick.tech/micahcarrick-posts/aerospike-summit20-enterprise-database-security/aerospike-data-protection-secrets-management.png)

On any given Aerospike server node you may have TLS private keys, encryption-at-rest keys, external authentication (LDAP) credentials, and Cross-Datacent Replication (XDR) credentials. All of these secrets must be protected.

These secrets are essentially bits of configuration that you are managing. They are keys and passwords that need to be available to the Aerospike process (`asd`) at startup or at runtime. Once those secrets make it to the server your OS hardening and system access controls are in place to protect them. However, the challenge is in managing the full lifecycle of those secrets. They have to be created, they have to get deployed onto the servers, they may need to be revoked, and they will need to be rotated periodically.

This is a problem well suited for _secrets management_ tools. Most enterprise security platforms have secrets management built in, all the major cloud providers have dedicated secrets management services, and open-source tools like [Vault by Hashicorp](https://www.vaultproject.io/) have a vast array of Enterprise features and wide adoption. So let’s discuss a couple of patterns for using secrets management for Aerospike keys and credentials.

The first pattern, shown as the top-half of the diagram above, is to integrate secrets management software into the configuration management workflow. For example, config management tools such as Ansible, Chef, Puppet, etc. can be set up to bring in secrets from the secret store when configuring a node. Aerospike loads the secrets from the filesystem and is completely decoupled from the secrets management system. This has the advantage of being straightforward to setup and compatible with just about any secrets management tool out there. However, it does result in any given secret being in 2 locations; once in the secret store and once on the Aerospike server. Secret lifecycle management for Aerospike secrets is always a 2-step process of updating the secret store and then running the configuration management tool.

The second pattern, shown as the bottom-half of this diagram, is for Aerospike to integrate directly with the secrets management system. However, this requires Aerospike compatibility with a specific secret store. At this point in time Aerospike supports just one direct integration with a secrets management platform and that is the [Vault Integration with Aerospike](https://www.hashicorp.com/integrations/aerospike/vault). Vault in turn integrates with a large number of other systems.

This pattern has the advantage of centrally managing secrets. When implemented correctly it lowers the credential management burden and lowers the risk of compromised secrets.

However, being a direct integration, this pattern requires that the secret store is able to meet availability and scalability requirements. This means that this pattern is going to be a more complex architecture.


## Further Reading

* [Aerospike - Configuring Encryption at Rest](https://www.aerospike.com/docs/operations/configure/security/encryption-at-rest/index.html)
* [Aerospike - Hashicorp Vault Integration](https://www.aerospike.com/docs/operations/configure/security/vault/index.html)

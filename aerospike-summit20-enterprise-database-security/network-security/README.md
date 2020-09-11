In the **Enterprise Database Security** session I presented at [Aerospike Summit 2020](https://www.aerospike.com/summit/) I gave an overview of network security with Aerospike Enterprise.

_[Download presentation PDF](https://cdn.carrick.tech/micahcarrick-posts/aerospike-summit20-enterprise-database-security/Aerospike%20Summit%202020%20-%20Enterprise%20Database%20Security.pdf)_

***

To provide context, refer to the following diagram depicting an Aerospike deployment.

![Aerospike Deployment Diagram](https://cdn.carrick.tech/micahcarrick-posts/aerospike-summit20-enterprise-database-security/aerospike-network-security-deployment.png)

On the left we have developers building applications and back office jobs that will use an Aerospike database.

In the middle we have an Aerospike cluster managed by one or more administrative groups such as SREs, DevOps, DBAs, etc.

And on the right we have downstream systems which ingest and analyze security events and log data for use by information security teams.

The red arrows highlight where there is network connectivity between the Aerospike database and other systems or users as well as connectivity in between individual Aerospike nodes. This is where we need to apply network security.


## Firewall Rules

First, let's look at firewall rules adhering to the _principle of least privilege_ in which the firewall blocks all traffic and then rules are opened up to allow network access to only as needed.

For an Aerospike cluster there are 4 types of network traffic that needs to be allowed.

First, every Application node must be allowed to open up a TCP connection to every Aerospike node on the **_service_** port. This is port `3000` by convention but all Aerospike network settings can be configured.

![Aerospike Service Connections](https://cdn.carrick.tech/micahcarrick-posts/aerospike-summit20-enterprise-database-security/aerospike-network-security-allow-service.png)

The simple and more common way to setup these firewall rules is to allow the CIDR range for the _Application_ network to open TCP connections to the CIDR range for the _Aerospike_ network:

| Rule   | Type  | Port  | Source            | Destination  |
|--------|-------|-------|-------------------|--------------|
| ALLOW  | TCP   | 3000  | 192.168.128.0/25  | 10.0.1.0/25  |

However, some security models might require each IP address to be _explicitly_ allowed:

| Rule   | Type  | Port  | Source         | Destination |
|--------|-------|-------|----------------|-------------|
| ALLOW  | TCP   | 3000  | 192.168.128.1  | 10.0.1.1    |
| ALLOW  | TCP   | 3000  | 192.168.128.1  | 10.0.1.2    |
| ALLOW  | TCP   | 3000  | 192.168.128.2  | 10.0.1.1    |
| ALLOW  | TCP   | 3000  | 192.168.128.2  | 10.0.1.2    |

***

The next type of network traffic to allow are the **_heartbeat_** connections between each Aerospike node. This is the [clustering protocol](https://www.aerospike.com/docs/operations/configure/network/heartbeat/) in mesh mode which allows the Aerospike nodes to form a cluster.

![Aerospike Heartbeat Connections](https://cdn.carrick.tech/micahcarrick-posts/aerospike-summit20-enterprise-database-security/aerospike-network-security-allow-heartbeat.png)

Every Aerospike node must be allowed to open a TCP connection to every other Aerospike node on the heartbeat port which is 3001 by convention.

The common rule to allow the heartbeat connectivity in the Aerospike CIDR range:

| Rule   | Type  | Port  | Source      | Destination  |
|--------|-------|-------|------------ |--------------|
| ALLOW  | TCP   | 3001  | 10.0.1.0/25 | 10.0.1.0/25  |

Alternatively, the rules to allow explicit IP addresses for Aerospike nodes:

| Rule   | Type  | Port  | Source    | Destination |
|--------|-------|-------|-----------|-------------|
| ALLOW  | TCP   | 3000  | 10.0.1.1  | 10.0.1.2    |
| ALLOW  | TCP   | 3000  | 10.0.1.2  | 10.0.1.1    |

***

The third type of network traffic to allow are the **_fabric_** connections between each Aerospike node. This connectivity allows data to transfer between the nodes for replication and "migrations" (redistribution of data).

![Aerospike Fabric Connections](https://cdn.carrick.tech/micahcarrick-posts/aerospike-summit20-enterprise-database-security/aerospike-network-security-allow-heartbeat.png)

Every Aerospike node must be allowed to open a TCP connection to every other Aerospike node on the fabric port which is 3002 by convention.

The common rule to allow the fabric connectivity in the Aerospike CIDR block range:

| Rule   | Type  | Port  | Source      | Destination  |
|--------|-------|-------|------------ |--------------|
| ALLOW  | TCP   | 3002  | 10.0.1.0/25 | 10.0.1.0/25  |

Alternatively, the rules to allow explicit IP addresses for Aerospike nodes:

| Rule   | Type  | Port  | Source    | Destination |
|--------|-------|-------|-----------|-------------|
| ALLOW  | TCP   | 3002  | 10.0.1.1  | 10.0.1.2    |
| ALLOW  | TCP   | 3002  | 10.0.1.2  | 10.0.1.1    |

Notice that the fabric rules are identical to the heartbeat rules except for the port. If the configured ports are sequential then the rules for heartbeat and fabric can be combined for firewalls that allow specifying port ranges:

| Rule   | Type  | Port       | Source      | Destination  |
|--------|-------|------------|------------ |--------------|
| ALLOW  | TCP   | 3001-3002  | 10.0.1.0/25 | 10.0.1.0/25  |

***

The fourth and final type of network traffic is only applicable for deployments which are using [Cross Datacenter Replication (XDR)](https://www.aerospike.com/docs/architecture/xdr.html) to replicate data between Aerospike clusters in different data centers or cloud regions.

![Aerospike XDR Connections](https://cdn.carrick.tech/micahcarrick-posts/aerospike-summit20-enterprise-database-security/aerospike-network-security-allow-xdr.png)

XDR traffic uses the same service connections that applications use. That means that every Aerospike node in the XDR source cluster must be allowed to open a TCP connection to every Aerospike node on the **_service_** port which is 3000 by convention.

The rule to allow traffic from the XDR source cluster to the XDR destination cluster using CIDR blocks:

| Rule   | Type  | Port  | Source      | Destination   |
|--------|-------|-------|------------ |---------------|
| ALLOW  | TCP   | 3000  | 10.0.1.0/25 | 172.16.0.0/25 |

Alternatively, the rules to allow explicit IP addresses:

| Rule   | Type  | Port  | Source    | Destination |
|--------|-------|-------|-----------|-------------|
| ALLOW  | TCP   | 3000  | 10.0.1.1  | 172.16.0.1  |
| ALLOW  | TCP   | 3000  | 10.0.1.1  | 172.16.0.2  |
| ALLOW  | TCP   | 3000  | 10.0.1.2  | 172.16.0.1  |
| ALLOW  | TCP   | 3000  | 10.0.1.2  | 172.16.0.2  |

Notice that the xdr rules are identical to the service rules except for the source being the XDR source instead of the Application nodes. The rules for service and xdr can be combined for firewalls that allow specifying multiple CIDR/IP ranges:

| Rule   | Type  | Port       | Source                         | Destination  |
|--------|-------|------------|--------------------------------|--------------|
| ALLOW  | TCP   | 3000       | 172.16.0.0/25,192.168.128.0/25 | 10.0.1.0/25  |


## Encryption in Transit (TLS)

The second part of securing the network is about using TLS to encrypt data in transit and ensure connections are only established with trusted machines on the network.

### TLS Certificates

We just looked at the 4 types of network connectivity: **_service_**, **_heartbeat_**, **_fabric_**, and **_XDR_**. Aerospike can be configured to use TLS on each of those types of network connections independently.

![Aerospike TLS Encryption](https://cdn.carrick.tech/micahcarrick-posts/aerospike-summit20-enterprise-database-security/aerospike-network-security-tls-encryption.png)

The **_service_** connections support standard or mutual authentication TLS also referred to as mTLS.

Both modes encrypt the data in transit, however, with standard TLS, only the Aerospike nodes authenticate themselves to the application nodes. With mutual TLS, the Aerospike nodes authenticate themselves to the application nodes who also authenticate themselves to the Aerospike nodes. So it’s a 2-way authentication.

A “bad actor” that found its way into the network somehow, could not pretend to be an application node nor pretend to be an Aerospike node without possessing the correct private key.

***

When TLS is enabled on the **_fabric_** or **_heartbeat_** connections, they will _always_ use what amounts to mutual authentication for those Aerospike-to-Aerospike connections. So once again, if a “bad actor” somehow breaches the private network, they could not pretend to be another Aerospike node in the cluster nor decrypt any of the data transferring between nodes without possessing the appropriate private key.

***

If you recall, **_XDR_** connectivity is actually just using the service connections. So with XDR, the source cluster acts as the TLS clients, much like the application nodes, and the destination cluster acts as the TLS servers.

***

Now, all of these _types of connections_ are generally configured to use the same server certificate as they are the same servers, however, they can technically be configured to have separate certificates.

Additionally, every Aerospike node can be configured to use the same certificate, meaning the entire cluster shares that certificate, or every node can be set up with it’s own unique certificates.

So that gives us three dimensions to work with; Standard vs. mutual TLS on the service connections, individual or shared certificates on each type of connection, and individual or shared certificates on each Aerospike server node.

Obviously, standard TLS with a single cluster-wide certificate is the simplest in terms of setup and management complexity. And if you’ve spent much time dealing with certificate lifecycle management, one certificate certainly sounds more pleasant to manage than dozens, hundreds, or thousands. And indeed it is.

But for organizations adopting more of a “zero trust” model, perhaps within environments dealing with highly sensitive data, on networks which the organization has deemed as untrusted such as the public cloud, unique certificates on each node may be required.

However, most enterprise use cases will fall somewhere in between these two extremes and the flexibility of Aerospike’s TLS configuration will allow it to be tailored to the specific needs of the organization, the environment, and the use case.

### TLS Cipher Suites

A cipher suite is a set of algorithms that are used in various phases during the TLS communication. The protocol allows for the client and server to negotiate which set of these algorithms both sides support.

Every TLS connection I described in the previous section can be configured as to which cipher suites are allowed and in what priority.

Without going too deep into the weeds about TLS cipher suites, let me just make two points about selecting TLS cipher suites to use with Aerospike Enterprise.

![Aerospike TLS Cipher Suites](https://cdn.carrick.tech/micahcarrick-posts/aerospike-summit20-enterprise-database-security/aerospike-network-security-tls-ciphers.png)

**_Point #1_**

Unlike a public, internet-facing application, many Aerospike deployments are done in environments where the organization is in control of both the client and the server. That means that compatibility with public clients like web browsers is not a factor and the list of allowed cipher suites can be narrowed down to just the more current algorithms which provide the best security and performance.

At the time of this presentation, that is highly likely to mean a cipher suite using AES encryption, which has hardware acceleration built-in to modern CPUs, using Galois Counter Mode or GCM, which also typically out-performs previous block cipher modes.


**_Point #2_**

Aerospike uses OpenSSL and thus configuring the cipher suite uses the OpenSSL notation. This is recognizable by the use of hyphens as shown in the top line in the image. Other tools and libraries, such as Java, may use the IANA notation. This is recognizable by the use of underscores as shown in the second line here. This means that specifying the cipher suites in Aerospike configuration may use a different notation that other sources you may be referencing.

You can read more about that in [How to select TLS cipher suites in Java](https://discuss.aerospike.com/t/how-to-select-tls-cipher-suites-in-java/7311).


## Further Reading

* [Aerospike - General Network Configuration](https://www.aerospike.com/docs/operations/configure/network/general/index.html)
* [Aerospike - TLS Configuration](https://www.aerospike.com/docs/operations/configure/network/tls/index.html)
* [Aerospike - Index of TLS Knowledge Base Articles](https://discuss.aerospike.com/t/all-about-configuration-for-tls/7543)

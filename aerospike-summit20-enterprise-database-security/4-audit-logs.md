In the **Enterprise Database Security** session I presented at [Aerospike Summit 2020](https://www.aerospike.com/summit/) I gave an overview of data protection with Aerospike Enterprise.

_[Download presentation PDF](https://cdn.carrick.tech/micahcarrick-posts/aerospike-summit20-enterprise-database-security/Aerospike%20Summit%202020%20-%20Enterprise%20Database%20Security.pdf)_

***


To provide context, refer to the following diagram depicting an Aerospike deployment.

![Aerospike Deployment Diagram](https://cdn.carrick.tech/micahcarrick-posts/aerospike-summit20-enterprise-database-security/aerospike-security-event-audit-deployment.png)

Once all the enterprise security fetures have been implemented, how do we verify we’re doing any of this right? How do we get visibility into what’s happened in the past and how do we respond to events as they happen in real time?

## Security Event Architecture

The diagram below is depicting an Aerospike node on the left producing a security audit trail and shipping that to a downstream system via syslog. The rest of this diagram is just one of many types of architectures for consuming Aerospike audit logs. I’ll talk this one through to give you an idea of what’s happening.





## Further Reading

* [Aerospike - Audit Trails](https://www.aerospike.com/docs/operations/configure/security/access-control/index.html#audit-trails)

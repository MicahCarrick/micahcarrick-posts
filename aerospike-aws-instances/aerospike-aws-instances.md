_How I select the optimal AWS instance type for running Aerospike_

***

One of the most common conversations I have when providing [consulting services](https://www.aerospike.com/consulting-services/) for Aerospike customers running on AWS is about how to select the optimal AWS instance type.

* Which instance provides the lowest latency?
* Do I need a "storage optimized" instance type?
* Should I use EBS?
* Can I use a cheaper instance type?

When it comes to running production Aerospike workloads at scale on AWS I generally only look at a this short list of instance families:

| Instance Family  | Strengths                                                 |
-------------------|-----------------------------------------------------------|
| i3en instances   | All the things! Big and fast with lots of storage         |
| i3 instances     | Lots of storage at a low cost                             |
| r5/r5d instances | Fast with lowest cost per GB of DRAM                      |
| c5d instances    | Very fast and low cost per vCPU                           |
| m5d instances    | Low-latency all-rounder                                   |


So let's look closer at what I consider when selecting AWS instance types for Aerospike customers and then what each of these instance families is good at and where it might fall short.

***

## Instance Type Considerations

None of the technical considerations matter without cost. If price were no object I'd just say run Aerospike on a big ol' cluster consisting of the beefy `i3en` instances and be done with it.

But alas, we live in the real world...


### Storage

The first consideration for Aerospike on AWS is storage. Aerospike's [Hybrid Storage](https://www.aerospike.com/docs/architecture/storage.html) configured to use SSD/Flash is going to be used in the vast majority of use cases.

This means I want fast, consistent, and reliable NVMe SSD storage. Amazon's network-attached storage, Elastic Block Store (EBS), does not meet that need. EBS is fantastic for many storage needs, but it is not fast, consistent, or reliable when milliseconds matter. No, what I need is Amazon's [SSD instance store volumes](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ssd-instance-store.html).

But, not all instance store volumes are equal. Aerospike has [certified the throughput of AWS SSD volumes](https://www.aerospike.com/docs/operations/plan/ssd/ssd_certification.html#cloud-based-flash) for various instance families. This provides a good baseline for the relative performance expected from any given instance type.

As a general rule I try to avoid instance sizes that don't make use of a full sized SSD for a given family. That means that I try not to go smaller than the smallest instance type within a family that has the same size SSD as the largest in that family (half-size instances and above). This is to avoid sharing the physical SSD with other tenants on the underlying AWS host.


### Memory

When Aerospike's Hybrid Storage is configured to store data in memory then the RAM is obviously the primary factor in the instance's storage capacity. When configured to store primary indexes in memory it's still a key factor, but, with some nuance.

Aerospike's primary indexes are a fixed size (64 bytes) per object. That means that if I am storing a large amount of small objects then I need a higher memory-to-disk ratio than if I have fewer large objects.

I also want to condider optional features than can leverage RAM such as [read page cache](https://www.aerospike.com/docs/reference/configuration/index.html#read-page-cache) and [secondary index](https://www.aerospike.com/docs/architecture/secondary-index.html).


### Network

The oft-overlooked network capacity is very important in cloud environments. 

Obviously the network throughput and latency is an important consideration. However, there is also [clustering](https://www.aerospike.com/docs/architecture/clustering.html) and the application's usage pattern to consider. Does the application have an aggressive SLA? How will it behave when the network is down? What about when the network is slow or dropping packets?

So a more consistent and reliable network results in a more stable cluster. Sure, Aerospike will automatically handle nodes leaving the cluster due to a flakey network, however, that self-healing means replicating data and replicating data means spending money on data transfer.

This means instance _size_ matters in addition to the type. When I'm looking at the [AWS instance type documentation](https://aws.amazon.com/ec2/instance-types/) I'm paying special attention to the "Networking Performance" column. When the value is "up to X" then it's a bursty shared network allocation and the [noisy neighbor effect](https://en.wikipedia.org/wiki/Cloud_computing_issues#Performance_interference_and_noisy_neighbors) will be more pronounced.


### CPU

I avoid the "burstable" general-purpose instance families like the `t2`/`t3` instances for production workloads. It's too risky to be able to accidentally push up above the baseline performance and have unexpected disruptions when CPU credits run dry from bursting.

But beyond that, CPU is rarely a primary consideration in selecting the right instance type. As instance types are sized up to accomodate storage, memory, or network, I more often find CPU to be under-utilized.

This is an opportunity for optimization as there are a number of optional features that can take advantage of under-utilized CPU:

* TLS encryption in transit and encryption at rest can improve security (IMHO encryption should be the rule, not the exception).
* Storage compression can reduce overall storage capacity which means more cost savings.
* Client-server compression on the wire can save money on AWS ingress/egress costs.
* Taking advantage of the rich set of APIs available for complex-data types (CDTs) can optimize for both cost and performance by offloading some of the data manipulation to the Aerospike nodes.

So, for use cases that are not using these features I consider whether or not there is an opportunity to make use of more CPU to optimize for cost, performance, or both. And then of course the inverse is also true. I make sure to consider CPU for use cases that are using these features.


## Instance Type Selection

The _storage optimized_ instances are the obvious contender. Both the older `i3` and the shiny new `i3en` instance families are viable. But, the _compute optimized_ `c5` instances and the _memory optimized_ `r5` are great options depending on the use case, and the `m5` instances are a solid choice from the _general purpose_ category.


### i3en Instances

When talking about _storage optimized_ AWS instances the `i3en` is the big dog. I was pretty excited about these when AWS announced them just last year.

First, they have a huge amount of SSD capacity at the lowest cost per GB. The largest `i3en.24xlarge` weighs in at whopping 8 x 7.5 TB SSD volumes for 60 TB of storage per instance at ~$1.58 per GB per year¹.

Second, they have pretty fast drives. [We've clocked one of these SSD drives at 162k TPS](https://www.aerospike.com/docs/operations/plan/ssd/ssd_certification.html#cloud-based-flash). When compared to the `i3` at 33k TPS that's a significant improvement!

When compared with the older `i3` instances, these instances have more SSD storage at a lower cost per GB, more SSD throughput, more CPU, more network, and more RAM. So... moar!

The down sides are that being relatively new they may not be available in all regions and they have a higher cost per GB of RAM than _memory optimized_ `r5` instances.

I like the `i3en` instances for low-latency workloads storing large amounts of data with a memory-to-disk ratio on the `i3en` instances that results in a storage-bound cluster. In other words, when the number of instances is selected based on how much data needs to be stored and the indexes will fit into the available memory.

I also like the `i3en` instances for a configuration in which indexes are stored on the SSD as well as the data ("all flash"). This allows for HUGE amounts of data (think hundreds of TB and beyond) without breaking the bank on DRAM.

For the best performance the [SSD disks should be over-provisioned](https://www.aerospike.com/docs/operations/plan/ssd/ssd_op.html) 20%.


### i3 Instances

Before the `i3en` instances hit the scene these were the kings of SSD capacity. The largest `i3.16xlarge` instance has 8 x 1.9 TB SSD volumes. That's 15.2 TB of storage per instance at ~$2.88 per GB per year¹.

They also have a very good cost per GB of RAM.

The down side is the drives are substantially slower and they have less vCPU than all the other instance families being considered. In short, they are the slowest.

I like the `i3` instances when `i3en` is not available and storing large amounts of data. With a fairly low cost per GB of RAM _and_ a fairly low cost per GB of SSD storage, I also like the `i3` as a cost-effective all-rounder for lower throughput workloads.

For the best performance the [SSD disks should be over-provisioned](https://www.aerospike.com/docs/operations/plan/ssd/ssd_op.html) 20%.


### r5 and r5d Instances

The _memory optimized_ `r5` instances provide the best cost per GB of RAM which makes them the ideal for when Aerospike is configured as an in-memory database. The largest `r5.24xlarge` instances have 768 GB of RAM per instance at ~$78.84 per GB per year.

However, the `r5d` variant also adds 4 x 900 GB SSD volumes for a total of 3.6 TB per instance. These are fairly fast SSD drives which we've clocked at 138k TPS.

The down side is that the `r5d` variant has the _highest_ cost per GB of SSD storage of all the instance types considered here.

I like the `r5` instances for running Aerospike as an in-memory database and I like the `r5d` instances for low-latency use cases where the memory-to-disk ratio results in a memory-bound cluster.


### c5d Instances

The _compute optimized_ `c5d` instances are all about speed. When latency is the be-all/end-all these are the front runner. They have the most powerful CPUs and the SSD volumes are very fast.

The down sides are that they have the highest cost per GB of RAM by a wide margin and max out at 192 GB RAM per instance.

I like the `c5d` instances when the use case is very latency sensitive, is making use of CPU heavy features of Aerospike (encryption, compression, CDTs, etc.), and the memory-to-disk ratio does not result in a memory-bound cluster.


### Instance Comparison

To do an objective comparison of these instance types based on a specific workload with specific performance requirements, I refer to the following resources:

* [Amazon Instance Types](https://aws.amazon.com/ec2/instance-types/) and [Amazon EC2 Pricing](https://aws.amazon.com/ec2/pricing/) provide up-to-date specs on the various instances and current pricing respectively.
* [Aerospike Cloud-Based Flash ACT Results](https://www.aerospike.com/docs/operations/plan/ssd/ssd_certification.html#cloud-based-flash) provides some baseline TPS numbers for various instances, however, I typically do a custom test using the open-source [Aerospike Certification Tool (ACT)](https://github.com/aerospike/act). This is the only way to get an accurate profile of the SSD's performance profile for a specific workload.
* [Aerospike Capacity Planning Guide](https://www.aerospike.com/docs/operations/plan/capacity/) provides details on how to calculate the RAM, SSD storage, and SSD throughput needs for a specific workload.

The following table compares the maximum size instance types for each family on my short list. The cost is broken down into annual cost per some unit of capacity. This makes it easy to make a first pass at which instance familiy is going to be a good fit for a specific workload.


| Instance         | vCPU |     SSD |   DRAM |   TPS² |  Hourly | per GB SSD   | per GB DRAM   | per 1k TPS²   |
| -----------------|------|---------|--------|--------|---------|--------------|---------------|---------------|
| `i3en.24xlarge`  |   96 | 60.0 TB | 768 GB | 1,296k | $10.848 |  $1.58 /year | $123.74 /year |  $73.32 /year |
| `i3.16xlarge`    |   64 | 15.2 TB | 488 GB |   264k |  $4.992 |  $2.88 /year |  $89.61 /year | $165.64 /year |
| `r5d.24xlarge`   |   96 |  3.6 TB | 768 GB |   552k |  $6.912 | $16.82 /year |  $78.84 /year | $109.69 /year |
| `c5d.24xlarge`   |   96 |  3.6 TB | 192 GB |   564k |  $4.608 | $11.21 /year | $210.24 /year |  $71.57 /year |
| `m5d.24xlarge`   |   96 |  3.6 TB | 384 GB |   432k |  $5.424 | $13.20 /year | $123.74 /year | $109.99 /year |

For example:

* A high-throughput workload without a small amount of data is likely to be most cost effective on `c5d` instances as they have a low cost per 1k TPS.
* A high-throughput workload with a very large amount of data is likely to be most cost effective on `i3en` instances as they have a low cost per 1k TPS but also have a lot of SSD storage.
* A high-throughput workload with a lot of small objects, and thus a high memory-to-disk ratio, is likely to be most cost effective on `r5d` instances as they have a low cost per GB of DRAM.
* A low-throughput workload with a lot of data with a moderate/high number of objects is likely to be most cost effective on `i3` instances as they have both low cost per GB of DRAM as well as low cost per GB of SSD storage. 


***

¹ _Cost estimates based on largest instance type in family using the full list pricing for on-demand instances in us-east-1 as of September 2020_

² _Per-instance TPS based on a single drive multiplied by total drives per instance. See details and caveats at [Cloud-Based Flash ACT results](https://www.aerospike.com/docs/operations/plan/ssd/ssd_certification.html#cloud-based-flash)_


## Scaling Strategy (Instance Size vs. Cluster Size)

The instance type selection pointed out that the smaller end of the sizes within an instance family have bursty network and shared SSD controllers due to the amount of other tenants on the host. What this amounts to is these instance sizes will have more _variability_ in their performance characteristics.

For smaller workloads there must be a trade off between larger instance sizes and larger cluster sizes. The consideration here is about having enough instances in the cluster to spread the workload out which lessens the impact of single instance maintenance or failure versus minimizing the variability of the performance. On the other end of the spectrum as the cluster grows more nodes can mean longer maintenance for rolling updates and larger instances mean slower cold restarts as indexes are being rebuilt.

There is no hard and fast rule here and these considerations must be taken in context of each organization's budget and operational parameters, however, the approach I take for production clusters is loosely:

1. Prefer a cluster size of 2x availability zones and don't go less than 1x
2. Prefer instance sizes with fixed network performance and don't go less than 4 vCPU

So that means if I'm designing a production cluster in 3 zones based on the `r5d` family the smallest cluster I would recommend is 3x `r5d.xlarge` (4vCPU).

The scaling strategy would be to scale _out_ to 6x `r5d.xlarge` to get to 2x zones after which it would then scale _up_ until it gets to the `r5d.8xlarge` which have the fixed network.

However, if the workload is latency sensitive and the variability of the small instances is a concern then the scaling strategy would insted be to scale _up_ from the minimum cluster size of 3 until it gets to 3x `r5d.8xlarge` where it has the fixed network. Then it would start scaling _out_ to 6x `r5d.8xlarge`.

Once reaching the point of 6x `r5d.8xlarge` scaling _up_ to the `r5d.12xlarge` would be the next step to get to the full-size SSD (not shared). After that the decisions to continue to scale _up_ vs. _out_ are largely dependent on the opertational parameters that best suite the organization.


***

## Conclusion

The art of selecting the right instance type is about optimizing the cost to performance ratio.

One of the beautiful things about running Aerospike in the cloud is that you don't have to get it perfect on day one. You can start with a conservative approach in which you leave room for the application usage patterns to evolve and stabilize before right-sizing based on real-world production metrics. Remember, with Aerospike you can always do rolling updates, with zero downtime, to switch between instance sizes and types or do A/B testing.

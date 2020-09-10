---
title: Serialized or Compressed Objects with Aerospike? Consider carefully.
published: false
tags: aerospike, nosql, protobuf
#cover_image: [url]
---

_Make sure you consider these trade-offs before storing serialized or compressed blobs in Aerospike._

***

Serializing and compressing data client-side before storing it in a back-end database is a common pattern. I run into this frequently in my work with Aerospike customers, typically in the form of protocol buffers (protobuf) or gzipped JSON. After all, who doesn't want to reduce network bandwidth and storage?

However, unless the use case is a dumb-simple get/put cache, you may be trading off some powerful Aerospike functionality for very little gain - if any.

Some of the benefits of serializing and compressing objects client-side include the following:

* **Interoperability**: Application developers can work in language-native constructs and exchange objects in a language-agnostic format. 

* **Network bandwidth**: Getting and putting compressed objects that are compressed lower network bandwidth.

* **Storage space**: Storing objects that are compressed usually use less storage space disk.

These are all good things. However, Aerospike provides alternative mechanisms to achieve each of these benefits as well. [Aerospike client libraries](https://www.aerospike.com/docs/client/) allow application developers to work in language-native constructs for Aerospike data, [client policies](https://www.aerospike.com/docs/guide/policies.html) can enable compression on the network, and [storage compression](https://www.aerospike.com/docs/operations/configure/namespace/storage/compression.html) can be enabled and tuned.

Moreover, Aerospike will add some sensible logic and flexibility without any additional work in the applications.

* When compression is enabled Aerospike won't store objects compressed if the result is actually _larger_ when compressed.

* Compression comes at the cost of CPU. Applications can choose to compress data on the network on a _per-transaction_ basis and storage compression algorithm/level can be configured on a _per-namespace_ basis. This allows optimizing to get the most "bang for your buck" per use case.

So you may already be thinking: "Well, gosh, maybe I don't need to serialize all my objects client-side". But the real trade-off to consider is not about the fact that you get parity with Aerospike out-of-the-box, it's about _what you lose_ when storing serialized and/or compressed blobs in Aerospike.

* You will lose the ability to do [Predicate Filters](https://www.aerospike.com/docs/guide/predicate.html) on [queries](https://www.aerospike.com/docs/guide/query.html) and [scans](https://www.aerospike.com/docs/guide/scan.html) against the data in the blob

* You will lose the ability to leverage [Bitwise Operations](https://www.aerospike.com/docs/guide/bitwise.html)

* You will lose the ability to use the feature-rich Complex Data Type (CDT) API on [Lists](https://www.aerospike.com/docs/guide/cdt-list-ops.html) and [Maps](https://www.aerospike.com/docs/guide/cdt-map-ops.html)

Now those are some incredibly useful features - especially those CDT operations. Unless you know you only want a dumb get/put cache you don't want to miss out on those.

But you're a geek... I'm a geek... so let's see this in action with some quick 'n dirty Python.

***

## Serialized/Compressed Blobs vs Aerospike CDT Performance

As an example, assume a use case which rolls up all purchase transactions by day and stores them in records split by month and account number using a composite key like: `monthly:<YYYYMM>:<Account ID>`.

In Python, each record can be represented as standard dictionary with nested lists and dictionaries:

```
'monthly:201901:00001' {
  'acct': '00001',
  'loc': 1,
  'txns': {
    '20190101': [
      {
        'txn': 1,
        'ts': 50607338,
        'sku': 5631,
        'cid': "GFOBVQPRCZVT",
        'amt': 873300,
        'qty': 23,
        'code': 'USD'
      },
      { ... }
    ]
    '20190102': [ ... ]
  }
}
```

The `txns` key contains a dictionary where each key in that dictionary is the day of the month in `YYMMDD` format and the value is a list of every transaction for that day.

In order to highlight the pros and cons of serialization/compression client-side vs. using Aerospike's built-in features, two Aerospike namespaces are setup.

The first namespace `ns1` uses a file storage engine without any compression enabled. It will be used to store the records as blobs that have been serialized as JSON and compressed with zlib level 6 (default) in the Python code.

The `namespace` stanza in the `aerospike.conf` file looks like this:

```
namespace ns1 {
    replication-factor 1
    memory-size 2G

    storage-engine device {
        file /opt/aerospike/data/ns1.dat
        filesize 100M
    }
}
```

The second namespace `ns2` uses a file storage engine with ZStandard compression level 1 (least amount of compression, best performance). It will be used to store the records as Aerospike CDTs.

The `namespace` stanza in the `aerospike.conf` file looks like this:

```
namespace ns2 {
    replication-factor 1
    memory-size 2G

    storage-engine device {
    file /opt/aerospike/data/ns2.dat
    filesize 100M
    compression zstd
            compression-level 1
    }
}
```

Using the Python script called `generate-data.py`, dummy data is generated using the above data model and loaded into each of the two namespaces. It generates 2 years of historic transaction data for 10 accounts each doing 250 transactions per day.

Looking at just the section of `generate-data.py` that loads data into the two namespaces, the "blob" version first converts the Python object to JSON and then compresses the JSON string using zlib and then writes the record to `ns1` namespace. The "cdt" version just writes the Python object as-is to the `ns2` namespace.

```python
# write each record
start = time()
for pk, record in objects.items():

    if object_type == 'blob':
        record_data = {'object': zlib.compress(json.dumps(record).encode("utf-8"), zlib_level)}

    elif object_type == 'cdt':
        record_data = record

    key = (namespace, set_name, pk)
    client.put(key, record_data, 
            policy={'exists': aerospike.POLICY_EXISTS_CREATE_OR_REPLACE}
    )
elapsed = time() - start
```

After `generate-data.py`  loads the dummy objects into each of the Aerospike namespaces it outputs some statistics about that namespace:

```
$ python3 generate-data.py 
Aerospike:          127.0.0.1:3000 ns1.example
Run time:           9.354 seconds
Object type:        blob
Object count:       240
Avg object size:    217.0 KiB
Compression ratio:  -
---
Aerospike:          127.0.0.1:3000 ns2.example
Run time:           5.610 seconds
Object type:        cdt
Object count:       240
Avg object size:    182.5 KiB
Compression ratio:  0.349
---
```

So right away it is clear that using Aerospike native CDTs with compression enabled results in smaller objects (better storage compression) and loaded the data faster.

Some of this can be explained by the fact that (a) when Aerospike compresses the data it is using ZStandard compression instead of zlib which was used in the Python code and (b) Aerospike is built with a very fast, statically typed, compiled language (C lang) and our Python code is a slower, dynamically typed language running on an interpreter. So it is certainly not apples-to-apples.

However, the two key takeaways here, from the application development perspective, are that the Aerospike compression is essentially free and that you work in your native language types.


## Use Case: Correct Data with Background Read/Write Scan

To illustrate the value of being able to leverage advanced Aerospike features that are not available when doing client-side serialization/compression, let's take a look at a data correction use case. Suppose that there was a bug in the application that resulted in an incorrect value for the location (`loc`) for just one account (`acct`).

If the records are serialized and compressed client-side, application code would need to read every record back over the network, into the application RAM, deserialize and decompress it, make the correction, and then write the entire record back over the network.

However, if using Aerospike CDTs with server-side compression, the application can initiate a [background read/write scan](https://www.aerospike.com/docs/guide/scan.html) with a [predicate filter](https://www.aerospike.com/docs/guide/predicate.html) to do the work entirely on the Aerospike nodes.

An example of this is illustrated in the Python script `correct-data.py`. This script operates on the same data that was generated with `generate-data.py` above.

First, a predicate filter is setup which will filter records to only those that have an account ID (`acct`) of `00007` **AND** a current location ID (`loc`) value of `5`.

```python
account_to_correct = '00007'
incorrect_location = 5

predicate_expressions = [

    # push expressions to filter by loc=5
    predexp.integer_bin('loc'),
    predexp.integer_value(incorrect_location),
    predexp.integer_equal(),

    # push expression to filter by acct=00007
    predexp.string_bin('acct'),
    predexp.string_value(account_to_correct),
    predexp.string_equal(),

    # filter by the `loc` AND `acct` expressions
    predexp.predexp_and(2)
]

policy = {
    'predexp': predicate_expressions
}
```

Next, a background scan is sent to each Aerospike node using the above predicate expressions to filter the scan results and passing an array of write operations to perform on each resulting record. In this case, the write ops contains just one operation to update the location ID (`loc`) to `2`.


```python
correct_location = 2

# Do a background scan, which runs server-side, to update the records that
# match the predicate expression with the correct value for 'loc'.
ops =  [
    operations.write('loc', correct_location)
]

bgscan = client.scan(namespace, set_name)
bgscan.add_ops(ops)
scan_id = bgscan.execute_background(policy)
print("Running background read/write scan. ID: {}".format(scan_id))

# Wait for the background scan to complete.
while True:
    response = client.job_info(scan_id, aerospike.JOB_SCAN)
    if response["status"] != aerospike.JOB_STATUS_INPROGRESS:
        break
    sleep(0.25)
```

What's that? You're worried about that background read/write scan impacting performance? No worries, Aerospike has that covered by allowing you to throttle the records per second using the [background-scan-max-rps](https://www.aerospike.com/docs/reference/configuration/#background-scan-max-rps).


Consider all the opportunities to optimize cost and performance by sending lightweight binary _operations_ to the Aerospike database nodes rather than passing ~200k objects back and forth to be processed client-side. Think about how much money you could save! You'll be a hero!

***

* [View complete source code on Github](https://github.com/MicahCarrick/micahcarrick-posts/tree/master/aerospike-serialize-vs-cdt)
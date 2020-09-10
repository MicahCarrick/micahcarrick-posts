import aerospike
from aerospike import predexp
from aerospike_helpers.operations import operations
from datetime import timedelta, date, datetime
from time import sleep


def main():
    # variables to connect to Aerospike
    host = '127.0.0.1'
    port = 3000
    namespace = 'ns2'
    set_name = 'example'

    # variables to control which account and locations are corrected
    account_to_correct = '00007'
    incorrect_location = 5
    correct_location = 2

    # connect to Aerospike
    client = aerospike.client({'hosts': [(host, port)]}).connect()

    # only update records that match on 'acct' AND 'loc'
    predicate_expressions = [
        predexp.integer_bin('loc'),
        predexp.integer_value(incorrect_location),
        predexp.integer_equal(),
        predexp.string_bin('acct'),
        predexp.string_value(account_to_correct),
        predexp.string_equal(),
        predexp.predexp_and(2)
    ]

    policy = {
        'predexp': predicate_expressions
    }

    ops =  [
        operations.write('loc', correct_location)
    ]

    # Do a standard scan with the predicate expressions and count the results.
    scan = client.scan(namespace, set_name)
    records = scan.results(policy)
    print("{} records found".format(len(records)))

    # Do a background scan, which runs server-side, to update the records that
    # match the predicate expression with the correct value for 'loc'.
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

    # Do a standard scan with the predicate expressions and count the results.
    scan = client.scan(namespace, set_name)
    records = scan.results(policy)
    print("{} records found".format(len(records)))


if __name__ == "__main__":
    main()

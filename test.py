import io
import json

import jsonlines


RECORD_01 = {
    "eventTime": "2017-02-27T22:17:12Z",
    "requestParameters": {
        "AccessControlPolicy": {
            "AccessControlList": {
                "Grant": [
                    {
                        "Grantee": {
                            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                            "xsi:type": "CanonicalUser",
                            "DisplayName": "username",
                            "ID": "12345"
                        },
                        "Permission": "FULL_CONTROL"
                    },
                    {
                        "Grantee": {
                            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                            "xsi:type": "Group",
                            "URI": "http://acs.amazonaws.com/groups/global/AuthenticatedUsers"
                        },
                        "Permission": "READ_ACP"
                    }
                ]
            }
        }
    },
    "eventType": "AwsApiCall",
    "eventName": "PutBucketAcl",
    "recipientAccountId": "123456789012"
}

from memory_profiler import profile

@profile
def test_json_lines():
    records = [
        dict({'id': idx}, **RECORD_01) for idx in range(100)
    ]

    # Write the json lines to the object in minimal form
    json_lines = io.StringIO()
    with jsonlines.Writer(json_lines, compact=True) as writer:
        writer.write_all(records)
    # Get the result of the written lines
    # Keep line endings to make math easier and retain record validity
    records_json = json_lines.getvalue().splitlines(True)
     # Close the writer since we've read the data back
    json_lines.close()
    return records_json


@profile
def test_json():
    records = [
        dict({'id': idx}, **RECORD_01) for idx in range(100)
    ]
    # Write the json lines to the object in minimal form
    records_json = [
        json.dumps(record, separators=(',', ':')) + '\n' for record in records
    ]
    return records_json


def main():
    result = test_json_lines()
    result2 = test_json()

    print result == result2

if __name__ == '__main__':
    main()

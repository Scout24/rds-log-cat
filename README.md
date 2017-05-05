# rds-log-cat

Shipping RDS logs from s3 into a kinesis stream.
For example: This enables you to stream your logs into a elastic search cluster with kibana. Or any other logging/monitoring solutions.

This is in an early development stage ... not yet ready to use.

related projects:
- [RDS Log Dog](https://github.com/ImmobilienScout24/rds-log-dog) : AWS RDS Logs to s3

How this works
==============

rds-log-cat is a lambda function which can be triggered by a S3 bucket (on new files e.g.). It parses the logfiles and post it to kinesis.


How to install
==============

To build and test locally, simply execute:
   
    pyb
   
To build and deploy to AWS:
First configure the location, where to put the artifacts (lamdba and cloudformation stack) to:

    DISTRIBUTION_BUCKET_PREFIX=rds-log-cat

The AWS_DEFAULT_REGION will be added to the DISTRIBUTION_BUCKET_PREFIX like: rds-log-cat-eu-west-1

Build and deploy with the "teamcity" profile:
    
    pyb -o -E teamcity
   
At the end you will see, where the lambda is deployed to.
Now you can test the function in AWS with:

   ./run_integration_tests.py

If this succeeded you can deploy the cloudformation stack (see deployed artifacts).
Configuration is made in the description section of the function.

* kinesisStream - kinesis stream to post to
* type - type of logfile can be: postgresql or mysql

Example stacks can be found in [cfn/](tree/master/cfn/). See [README](tree/master/cfn/README.md) for how to deploy the stacks.

You can write your own parser to parse your logfiles (see below). 

How to use my own parser
========================

Create a python class with the name of your choice in
[parser/](tree/master/src/main/python/rds_log_cat/parser)

The class must implement at least the parse method from [Parser](tree/master/src/main/python/rds_log_cat/parser/parser)

Roll out the lambda with the config: type pointing to the name (without .py) of your created file.


Licence
=======

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

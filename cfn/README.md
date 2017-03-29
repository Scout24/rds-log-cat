Install
=======

This is manually work to do but we are working on a general one command solution ...

Dependencies
------------

- pybuilder
- cfn-sphere

Build and Deploy
--------------

If you not already have, build & deploy the lambda. You need to set the distribution bucket once:

    export DISTRIBUTION_BUCKET_NAME=[a bucket where to put the lambda zip]
    
For every build, execute these two lines:

    export BUILD_NUMBER=$((BUILD_NUMBER+1))
    pyb -o -E teamcity
    
Note the version and adopt the cloudformation parameter (lambdaFunctionS3Key) below.
Look for something like:
    
    [INFO]  Uploading to bucket "is24-pro-test-fborchers" key rds_log_cat_v0.1.5-8/rds_log_cat.zip


Creating the stack(s)
--------------------

If you developing w/o commiting to git, you have to set the following only once:

    export VERSION="v0.1.5"

Then deploy/update the stack with the new lambda zip:

    cf sync cfn/stacks.yaml -p rds-log-cat.lambdaFunctionS3Key=rds_log_cat_${VERSION}-${BUILD_NUMBER}/rds_log_cat.zip -p rds-log-cat.lambdaFunctionS3Bucket=${DISTRIBUTION_BUCKET_NAME}
    

If you run into trouble with the S3 bucket. There might be a circular dependency between the two stacks.
First try to create the lambda stack only! Then you should now be able to run the full stack(s) deployment.

Testing
-------


To test your deployment and the lambda itself, run the integration tests:

    pyb run_integration_tests

create .http files, requests, one only, for these tests:
    - every request start from the lab-core: http://localhost:8000/service-requests

        tests:
            1 - this test must call the reflab first time:  // this one is working
                - it must invoke the agent, check the docs
                - the docs are correctly, it build the json, and send to reflab, with success.


            2 - this is second test, and it must not call the agent, because its the same request, with different atributes values,
            but it already knows the structure, should also return success.  // this one is also working

            3 - the third test, must fail, and the fault must be the code base, sending wrong values:
                - so the agent must detect it
                - code base errors, they cannot be fixed, but they must be reported.



but the 3 one is not, first mistake is, I must able to simulate errors, without clearing the cache:
    - I must call the third request, without clearing any cache, I mean, I have many ways to send to the ref-lab a request, and it
    simply returns error, its mocking server:

        we have two the flow must be:
            - it prepares to send a request to ref-lab:
                - it searches in cache
                - it found cache
                - it sends the request, but it fails
                - so now I am in the agent, to see what error was that:
                    - and the error must be:
                        - code base errors, they cannot be fixed, but they must be reported.




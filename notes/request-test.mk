1 - this test must call the reflab first time:
    - it must invoke the agent, check the docs
    - the docs are correctly, it build the json, and send to reflab, with success.

2 - this is second test, and it must not call the agent, because its the same request, with different atributes values,
but it already knows the structure, should also return success.

3 - the third test, must fail, and the fault must be the code base, sending wrong values:
    - so the agent must detect it
    - code base errors, they cannot be fixed, but they must be reported.

4 — VitaCare, cache HIT, auth expired







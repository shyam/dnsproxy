## dnsproxy

**What does this do:**

This implements a DNS stub resolver. It listens on port 53 and resolve requests with an upsteam DNS server over TLS.

**Implementation notes:**

- It is a TCP to TCP+TLS forwarder written in Python. 
- Uses [maproxy](https://pypi.org/project/maproxy/) library for handling proxy operations. It internally allows Nonblocking Network I/O, by using python [tornado](https://github.com/tornadoweb/tornado) framework, an asynchronous networking library developed at FriendFeed. This allows the implementation to handle multiple requests simultaneously.
- Docker image at [my dockerhub](https://hub.docker.com/r/shyam/dnsproxy/).

**Running:**

````bash
$ docker run -d -p 5353:53 shyam/dnsproxy:latest 
74c80fa535b29e6562ffc76dd112f221c43322150f2bd59f75fb2ac83d36a180

$ docker ps
CONTAINER ID        IMAGE                    COMMAND                 CREATED             STATUS              PORTS                  NAMES
74c80fa535b2        shyam/dnsproxy:latest   "python dnsproxy.py"   8 seconds ago       Up 7 seconds        0.0.0.0:5353->53/tcp   festive_pike

$ docker logs festive_pike
[dnsproxy] tcp://127.0.0.1:53 -> tcp+tls://1.1.1.1:853

$ dig @localhost -p 5353 +tcp shyamsundar.org

; <<>> DiG 9.11.3-1ubuntu1.2-Ubuntu <<>> @localhost -p 5353 +tcp shyamsundar.org
; (1 server found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 23048
;; flags: qr rd ra; QUERY: 1, ANSWER: 4, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 1452
; PAD: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 
[ ... snip ... ]
..............................................................................................................")
;; QUESTION SECTION:
;shyamsundar.org.   IN  A

;; ANSWER SECTION:
shyamsundar.org.  1800  IN  A 185.199.109.153
shyamsundar.org.  1800  IN  A 185.199.110.153
shyamsundar.org.  1800  IN  A 185.199.111.153
shyamsundar.org.  1800  IN  A 185.199.108.153

;; Query time: 78 msec
;; SERVER: 127.0.0.1#5353(127.0.0.1)
;; WHEN: Wed Oct 03 15:06:44 CEST 2018
;; MSG SIZE  rcvd: 468

````

**Applications:**

* In a microservices environment -- service discovery is one of the most common paintpoints. When an org. is handling sensitive data like financial and medical records, we will need a way to ensure that even the DNS resolution which is integral to service discovery is secured and **resistant eavesdropping and tampering**. That is where a DNS stub proxy that allows existing services to work as-is without any major changes would help.

**Security Concerns and other areas of improvement:**

* Implement proper validation of SSL/TLS certificates including SPKI Pinning. 
  * This is particularly important to ensure that the upstream DNS service is not compromised. 

* Reduce latency by having long lived / persistent connections with upstream.

* TCP resolution can easily take up a lot of connections/open files. It has to be monitored and additional instances have to be setup so that this doesn't become a bottlenect.
  * Caching of dns responses could also help here, as it would not make sense to contact upstream each time.

* Refactor the application to be more modular and add test coverage.

* Ability to handle multiple upstream resolvers.
  * Will help in redundancy in case an upstream resolver goes offline.

* Ability to handle custom rules
  * There will always be cases where we would want to rewrite queries. Similar to the query rewriting capabilities of `coredns` and `dnsmasq`.

* Ability to handle UDP based DNS resolution.


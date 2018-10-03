## dnsproxy

**Problem statement:**

Implement a DNS stub resolver. It should listen on port 53 and resolve requests with an upsteam DNS server over TLS.

**Design notes:**

* After  reviewing the [Cloudflare's explanation of DNS over TLS](https://developers.cloudflare.com/1.1.1.1/dns-over-tls/) and [RFC7858](https://tools.ietf.org/html/rfc7858), it was clear that the implementation to start with will basically be a TCP to TCP+TLS forwarder.

* This assumption was validated with `socat` utility:

````bash
$ socat tcp-listen:2253,reuseaddr,fork openssl:1.1.1.1:853,cafile=/etc/ssl/certs/ca-certificates.crt,commonname=cloudflare-dns.com

$ dig @localhost -p 2253 +tcp shyamsundar.org

; <<>> DiG 9.11.3-1ubuntu1.2-Ubuntu <<>> @localhost -p 2253 +tcp shyamsundar.org
; (1 server found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 43130
;; flags: qr rd ra; QUERY: 1, ANSWER: 4, AUTHORITY: 0, ADDITIONAL: 1

[ ... snip ...]

;; QUESTION SECTION:
;shyamsundar.org.   IN  A

;; ANSWER SECTION:
shyamsundar.org.  773 IN  A 185.199.108.153
shyamsundar.org.  773 IN  A 185.199.109.153
shyamsundar.org.  773 IN  A 185.199.110.153
shyamsundar.org.  773 IN  A 185.199.111.153

;; Query time: 89 msec
;; SERVER: 127.0.0.1#2253(127.0.0.1)
;; WHEN: Wed Oct 03 15:23:51 CEST 2018
;; MSG SIZE  rcvd: 468

````

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
# dig @localhost -p 5353 +tcp shyamsundar.org

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

**Performance profiling:**

Any software to be used in productionshould be performance profiled for capacity planning and future optmization.

- The results below are for 30 clients over 30 seconds with 60 queries a second. 
- The results compared Stubby, socat and the python implementation here.
- All the three setups were using the same network conditions; pointing to the same upstream. Testing was done using [dnsperf-tcp](https://github.com/Sinodun/dnsperf-tcp). Queryfile used in this test is from (ftp://ftp.nominum.com/pub/nominum/dnsperf/data/queryfile-example-current.gz).

With smaller number of clients and smaller timeframe, the Average RTT is nearly same. However with some load (larger number of clients and timeframe), the deviation is visible. 

```
[*] using stubby

./dnsperf -d queryfile-example-current -l 30 -c 10 -Q 60 -z -p 9553
DNS Performance Testing Tool
Nominum Version 2.1.0.0

[Status] Command line: dnsperf -d queryfile-example-current -l 30 -c 10 -Q 60 -z -p 9553
[Status] Sending queries (to 127.0.0.1)
[Status] Started at: Wed Oct  3 23:44:54 2018
[Status] Stopping after 30.000000 seconds
[Status] Testing complete (time limit)

Statistics:

  Queries sent:         1800
  Queries completed:    1800 (100.00%)
  Queries lost:         0 (0.00%)

  Response codes:       NOERROR 1321 (73.39%), SERVFAIL 21 (1.17%), NXDOMAIN 458 (25.44%)
  Average packet size:  request 40, response 504
  Run time (s):         31.073661
  Queries per second:   57.926873
  TCP connections:      10
  Ave Queries per conn: 180

  Average RTT (s):      0.074498 (min 0.016354, max 4.274376)
  RTT StdDev (s):       0.276049


[*] using socat

./dnsperf -d queryfile-example-current -l 30 -c 10 -Q 60 -z -p 2253
DNS Performance Testing Tool
Nominum Version 2.1.0.0

[Status] Command line: dnsperf -d queryfile-example-current -l 30 -c 10 -Q 60 -z -p 2253
[Status] Sending queries (to 127.0.0.1)
[Status] Started at: Wed Oct  3 23:00:30 2018
[Status] Stopping after 30.000000 seconds
[Status] Testing complete (time limit)

Statistics:

  Queries sent:         1800
  Queries completed:    1800 (100.00%)
  Queries lost:         0 (0.00%)

  Response codes:       NOERROR 1319 (73.28%), SERVFAIL 23 (1.28%), NXDOMAIN 458 (25.44%)
  Average packet size:  request 40, response 97
  Run time (s):         31.639477
  Queries per second:   56.890953
  TCP connections:      10
  Ave Queries per conn: 180

  Average RTT (s):      0.075915 (min 0.012384, max 4.289669)
  RTT StdDev (s):       0.341624


[*] using the python implementation

$ ./dnsperf -d queryfile-example-current -l 30 -c 10 -Q 60 -z -p 2553
DNS Performance Testing Tool
Nominum Version 2.1.0.0

[Status] Command line: dnsperf -d queryfile-example-current -l 30 -c 10 -Q 60 -z -p 2553
[Status] Sending queries (to 127.0.0.1)
[Status] Started at: Wed Oct  3 22:58:41 2018
[Status] Stopping after 30.000000 seconds
[Status] Testing complete (time limit)

Statistics:

  Queries sent:         1800
  Queries completed:    1800 (100.00%)
  Queries lost:         0 (0.00%)

  Response codes:       NOERROR 1316 (73.11%), SERVFAIL 26 (1.44%), NXDOMAIN 458 (25.44%)
  Average packet size:  request 40, response 96
  Run time (s):         31.767947
  Queries per second:   56.660885
  TCP connections:      10
  Ave Queries per conn: 180

  Average RTT (s):      0.120437 (min 0.014077, max 4.884248)
  RTT StdDev (s):       0.387267
```

**Applications:**

* In a microservices environment -- service discovery is one of the most common paintpoints. When an org. is handling sensitive data like financial and medical records, we will need a way to ensure that even the DNS resolution which is integral to service discovery is secured and **resistant eavesdropping and tampering**. That is where a DNS stub proxy that allows existing services to work as-is without any major changes would help.

**Deployment Strategy:**

* It is very common to orchestrate microservices deployment using Kubernetes `(k8s)`. It is possible to run this application as a part of the system namespace `(kube-system)`. The cluster's upstream DNS resolution can be modified to use this as the upstream DNS resolver, or, even individual deployments/pod's could have  DNS policy that would use this.
  * Note: Since the implementation only supports TCP, we will have to configure the `/etc/resolv.conf` (libc) within the containers to ensure TCP based DNS resolution.

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

**Fun sidenote:**

`nginx` can also be setup to handle as tcp to tcp+tls reverse proxy. The following snippet added to nginx.conf was able to perform DNS resolution over TCP+TLS to cloudflare's DNS.

````
# nginx.conf
[...snip...]
stream {
  upstream cloudflare_dns_servers {
    server 1.1.1.1:853;
    server 1.0.0.1:853;
  }

  server {
    listen 1553;
    listen 1553 udp;
    proxy_responses 1;
    proxy_timeout 2s;
    proxy_ssl on;
    proxy_ssl_name "cloudflare-dns.com";
    proxy_ssl_protocols TLSv1.2;
    proxy_ssl_verify on;
    proxy_ssl_trusted_certificate /etc/ssl/certs/ca-certificates.crt;
    error_log /var/log/nginx/serror.log;
    proxy_pass cloudflare_dns_servers;
  }

  log_format stream  '$time_iso8601 $session_time '
                     '[$server_addr]:$server_port [$remote_addr]:$remote_port '
                     '$ssl_protocol$ssl_session_reused$ssl_cipher $ssl_server_name '
                     '$status $bytes_sent $bytes_received';

  access_log /var/log/nginx/stream.log stream;
}
[...snip...]
````

**Author:**

[Shyam Sundar C S](mailto:csshyamsundar@gmail.com) 
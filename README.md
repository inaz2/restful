# restful

RESTful file uploader over HTTPS and Basic auth


## Usage

### Change public directory permission

```
$ sudo chmod 777 public
```


### Generate self-signed certificate

```
$ openssl genrsa 2048 > cert.key
$ openssl req -x509 -new -days 3650 -key cert.key -subj "/CN=localhost" -out cert.crt
```


### Launch the server

The server requires root privledge, so use sudo as below:

```
$ sudo python restful.py 10443
```

If the port number is omitted, tcp/10443 is used.

The server runs with nobody:nogroup priviledge.


### Operate by curl

```
upload
$ curl -v -k -u admin -T foo.txt https://localhost:10443/

delete
$ curl -v -k -u admin -X DELETE https://localhost:10443/foo.txt

download
$ curl -v -k -u admin https://localhost:10443/foo.txt
```

### Operate by web browsers

`https://localhost:10443/post` shows alternative POST form to perform PUT/DELETE operation.

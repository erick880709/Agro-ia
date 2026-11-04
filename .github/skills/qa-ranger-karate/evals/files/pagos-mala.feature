@parallel=false
Feature: pagos

Background:
* url 'https://api-qa.banco.com/pagos'
* def clientSecret = 'sup3rS3cretValue'

Scenario: test 1
* path 'login'
* request { user: 'qa', password: 'Clave12345' }
* method post
* status 200
* def token = response.token
* header Authorization = 'Bearer ' + token
* def pagoId = 55
* def body = { id: pagoId, monto: 1000 }
* path 'pagos'
* request body
* method post
* status 201
* print response
* java.lang.Thread.sleep(5000)
* path 'pagos', pagoId
* method get
* status 200

Scenario: consulta en bd
* def fila = db.readRow("SELECT * FROM PAGOS WHERE ID = " + pagoId)
* match fila.ESTADO == 'OK'

Scenario: crear pago
* path 'pagos'
* request { monto: 10 }
* method post

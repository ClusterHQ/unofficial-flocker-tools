var http = require('http');
var concat = require('concat-stream')
var ecstatic = require('ecstatic')
var Router = require('routes-router')

var router = Router()

var server = http.createServer(router)

var nodes = require('./fixtures/nodes.json')

var fileServer = ecstatic({ root: __dirname })

router.addRoute("/v1/nodes", {
    GET: function (req, res) {
        res.end(JSON.stringify(nodes))
    }
})

router.addRoute("/v1/nodes/:id", {
    GET: function (req, res, opts) {
        var results = nodes.filter(function(node){
            return node.uuid.indexOf(opts.params.id)==0
        })
        res.end(JSON.stringify(results[0]))
    }
})

router.addRoute("/*", fileServer)

server.listen(8081, function(){
    console.log('server listening on port 8081')
})
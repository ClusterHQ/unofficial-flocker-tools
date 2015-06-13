var http = require('http');
var concat = require('concat-stream')
var ecstatic = require('ecstatic')
var Router = require('routes-router')

var router = Router()

var server = http.createServer(router)

var nodes = require('./fixtures/nodes.json')
var state = require('./fixtures/state.json')
var configuration = require('./fixtures/configuration.json')

var fileServer = ecstatic({ root: __dirname })

function crud(route, idfield, data){

    router.addRoute("/v1/" + route, {
        GET: function (req, res) {
            res.end(JSON.stringify(data))
        }
    })

    router.addRoute("/v1/" + route + "/:id", {
        GET: function (req, res, opts) {
            var results = data.filter(function(entry){
                return entry[idfield].indexOf(opts.params.id)==0
            })
            res.end(JSON.stringify(results[0]))
        }
    })
}

crud('nodes', 'uuid', nodes)
crud('configuration/datasets', 'dataset_id', configuration)
crud('state/datasets', 'dataset_id', state)

router.addRoute("/*", fileServer)

server.listen(8081, function(){
    console.log('server listening on port 8081')
})
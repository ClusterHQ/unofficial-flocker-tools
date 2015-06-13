/*global angular*/
(function () {
    "use strict";

    var DEBUG = true;
    //var BASE_URL = 'https://test.labs.clusterhq.com:4523/v1'
    var BASE_URL = 'v1/'
    //var BASE_URL = 'http://192.168.1.102:8088/v1/'

    var app = angular.module('myApp', ['ng-admin']);

    function getUrlMapper(base){
        return function(entityName, viewType, identifierValue, identifierName) {
                
            var url = base

            if(identifierValue){
                url += '/' + identifierValue
            }

            return url
            //return '/comments/' + entityName + '_' + viewType + '?' + identifierName + '=' + identifierValue; // Can be absolute or relative
        }
    }

    app.config(['NgAdminConfigurationProvider', 'RestangularProvider', function (NgAdminConfigurationProvider, RestangularProvider) {
        var nga = NgAdminConfigurationProvider;

        // truncate a long uuid to a short version
        function short_uuid(value) {
            return value.split('-')[0]
        }

        // use the custom query parameters function to format the API request correctly
        /*
        RestangularProvider.addFullRequestInterceptor(function(element, operation, what, url, headers, params) {
            if (operation == "getList") {
                // custom pagination params
                if (params._page) {
                    params._start = (params._page - 1) * params._perPage;
                    params._end = params._page * params._perPage;
                }
                delete params._page;
                delete params._perPage;
                // custom sort params
                if (params._sortField) {
                    params._sort = params._sortField;
                    delete params._sortField;
                }
                // custom filters
                if (params._filters) {
                    for (var filter in params._filters) {
                        params[filter] = params._filters[filter];
                    }
                    delete params._filters;
                }
            }
            return { params: params };
        });*/

        var admin = nga.application('Flocker GUI') // application main title
            .debug(DEBUG) // debug disabled
            .baseApiUrl(BASE_URL); // main API endpoint

        // define all entities at the top to allow references between them
        var node = nga.entity('nodes')
            .baseApiUrl(BASE_URL)
            .identifier(nga.field('uuid'))
            .readOnly()



        var configuration = nga.entity('configuration')
            .baseApiUrl(BASE_URL)
            .identifier(nga.field('dataset_id'))
            .url(getUrlMapper('configuration/datasets'))

        var state = nga.entity('state')
            .baseApiUrl(BASE_URL)
            .identifier(nga.field('dataset_id'))
            .readOnly()
            .url(getUrlMapper('state/datasets'))

        // set the application entities
        admin
            .addEntity(node)
            .addEntity(configuration)
            .addEntity(state)

        // customize entities and views

        node.dashboardView() // customize the dashboard panel for this entity
            .name('nodes')
            .title('Your nodes')
            .order(1) // display the post panel first in the dashboard
            .perPage(5) // limit the panel to the 5 latest posts
            .fields([
                nga.field('uuid').label('uuid').map(short_uuid),
                nga.field('host')
            ]); // fields() called with arguments add fields to the view

        configuration.dashboardView() // customize the dashboard panel for this entity
            .name('configuration')
            .title('Your configuration')
            .order(1) // display the post panel first in the dashboard
            .perPage(5) // limit the panel to the 5 latest posts
            .fields([
                nga.field('dataset_id').label('dataset_id').map(short_uuid)
            ]);

        state.dashboardView() // customize the dashboard panel for this entity
            .name('state')
            .title('Your state')
            .order(1) // display the post panel first in the dashboard
            .perPage(5) // limit the panel to the 5 latest posts
            .fields([
                nga.field('dataset_id').label('dataset_id').map(short_uuid)
            ]);

        node.listView()
            .title('All nodes') // default title is "[Entity_name] list"
            .description('Show the nodes in your cluster') // description appears under the title
            .infinitePagination(true) // load pages as the user scrolls
            .fields([
                nga.field('uuid').label('uuid').map(short_uuid), // The default displayed name is the camelCase field name. label() overrides id
                nga.field('host')
            ])
            .listActions(['show', 'edit', 'delete']);

        configuration.listView()
            .title('All configuration') // default title is "[Entity_name] list"
            .description('Show the configuration of volumes in your cluster') // description appears under the title
            .infinitePagination(true) // load pages as the user scrolls
            .fields([
                nga.field('dataset_id').label('dataset_id').map(short_uuid)
            ])
            .listActions(['show', 'edit', 'delete']);

        state.listView()
            .title('All state') // default title is "[Entity_name] list"
            .description('Show the state of volumes in your cluster') // description appears under the title
            .infinitePagination(true) // load pages as the user scrolls
            .fields([
                nga.field('dataset_id').label('dataset_id').map(short_uuid)
            ])
            .listActions(['show', 'edit', 'delete']);

        node.showView() // a showView displays one entry in full page - allows to display more data than in a a list
            .fields([
                nga.field('uuid').label('uuid').map(short_uuid), // The default displayed name is the camelCase field name. label() overrides id
                nga.field('host')
            ]);

        configuration.showView() // a showView displays one entry in full page - allows to display more data than in a a list
            .fields([
                nga.field('dataset_id').label('dataset_id').map(short_uuid)
            ]);

        state.showView() // a showView displays one entry in full page - allows to display more data than in a a list
            .fields([
                nga.field('dataset_id').label('dataset_id').map(short_uuid)
            ]);


        // customize header
        var customHeaderTemplate =
        '<div class="navbar-header">' +
            '<a class="navbar-brand" href="#" ng-click="appController.displayHome()">' + 
                //'<img src="images/clusterhq.png" />' +
                '<img src="images/logo.png" />' +
            '</a>' +
        '</div>';
        admin.header(customHeaderTemplate);

        // customize menu
        admin.menu(nga.menu()
            .addChild(nga.menu().title('Dashboard').icon('').link('dashboard').icon('<span class="glyphicon glyphicon-list-alt"></span>'))
            .addChild(nga.menu(node).icon('<span class="glyphicon glyphicon-file"></span>')) // customize the entity menu icon
            .addChild(nga.menu().title('Admin').icon('<span class="glyphicon glyphicon-cogwheel"></span>')
                .addChild(nga.menu(configuration).title('Configuration').icon('<span class="glyphicon glyphicon-star-empty"></span>')) 
                .addChild(nga.menu(state).title('State').icon('<span class="glyphicon glyphicon-star"></span>')) 
            )
        );

        nga.configure(admin);
    }]);

}());
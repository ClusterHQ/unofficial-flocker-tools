/*global angular*/
(function () {
    "use strict";

    var DEBUG = true;
    //var BASE_URL = 'https://test.labs.clusterhq.com:4523/v1'
    //var BASE_URL = 'v1/'
    //var BASE_URL = 'http://192.168.1.102:8088/v1/'
    var BASE_URL = 'v1/'

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

        var volume = nga.entity('datasets')
            .baseApiUrl(BASE_URL)
            .identifier(nga.field('dataset_id'))
            .url(getUrlMapper('datasets'))

        var configuration = nga.entity('configuration')
            .baseApiUrl(BASE_URL)
            .identifier(nga.field('dataset_id'))
            .readOnly()
            .url(getUrlMapper('configuration/datasets'))

        var state = nga.entity('state')
            .baseApiUrl(BASE_URL)
            .identifier(nga.field('dataset_id'))
            .readOnly()
            .url(getUrlMapper('state/datasets'))

        // set the application entities
        admin
            .addEntity(node)
            .addEntity(volume)
            .addEntity(configuration)
            .addEntity(state)

        // customize entities and views

        node.dashboardView() // customize the dashboard panel for this entity
            .name('nodes')
            .title('Your nodes')
            .order(1) // display the post panel first in the dashboard
            .perPage(5) // limit the panel to the 5 latest posts
            .fields([
                nga.field('host'),
                nga.field('uuid').label('uuid').map(short_uuid)
            ]); // fields() called with arguments add fields to the view

        volume.dashboardView() // customize the dashboard panel for this entity
            .name('volumes')
            .title('Your datasets')
            .order(1) // display the post panel first in the dashboard
            .perPage(5) // limit the panel to the 5 latest posts
            .fields([
                nga.field('primary', 'reference') // ReferenceMany translates to a select multiple
                    .label('Primary')
                    .targetEntity(node)
                    .targetField(nga.field('host')),
                nga.field('status'),
                nga.field('deleted', 'boolean'),
                nga.field('meta'),
                nga.field('size')
            ]);

/*
        configuration.dashboardView() // customize the dashboard panel for this entity
            .name('configuration')
            .title('Your configuration')
            .order(1) // display the post panel first in the dashboard
            .perPage(5) // limit the panel to the 5 latest posts
            .fields([
                nga.field('dataset_id').label('dataset_id').map(short_uuid),
                nga.field('deleted', 'boolean')
            ]);

        state.dashboardView() // customize the dashboard panel for this entity
            .name('state')
            .title('Your state')
            .order(1) // display the post panel first in the dashboard
            .perPage(5) // limit the panel to the 5 latest posts
            .fields([
                nga.field('dataset_id').label('dataset_id').map(short_uuid)
            ]);
*/
        node.listView()
            .title('All nodes') // default title is "[Entity_name] list"
            .description('Show the nodes in your cluster') // description appears under the title
            .infinitePagination(true) // load pages as the user scrolls
            .fields([
                nga.field('uuid').label('uuid').map(short_uuid), // The default displayed name is the camelCase field name. label() overrides id
                nga.field('host')
            ])
            .listActions(['show']);

        volume.listView()
            .title('All datasets') // default title is "[Entity_name] list"
            .description('Show the datasets in your cluster') // description appears under the title
            .infinitePagination(true) // load pages as the user scrolls
            .fields([
                nga.field('primary', 'reference') // ReferenceMany translates to a select multiple
                    .label('Primary')
                    .targetEntity(node)
                    .targetField(nga.field('host')),
                nga.field('status'),
                nga.field('deleted', 'boolean'),
                nga.field('meta'),
                nga.field('size')
                //status
                //meta
                //node
                //size
            ])
            .listActions(['show', 'edit'/*, 'delete'*/]);

        configuration.listView()
            .title('All configuration') // default title is "[Entity_name] list"
            .description('Show the configuration of datasets in your cluster') // description appears under the title
            .infinitePagination(true) // load pages as the user scrolls
            .fields([
                nga.field('dataset_id').label('dataset_id').map(short_uuid),
                nga.field('deleted', 'boolean'),
                nga.field('maximum_size'),
                nga.field('primary', 'reference') // ReferenceMany translates to a select multiple
                    .label('Node')
                    .targetEntity(node)
                    .targetField(nga.field('host'))
            ])
            .listActions(['show', 'edit', 'delete']);

        state.listView()
            .title('All state') // default title is "[Entity_name] list"
            .description('Show the state of datasets in your cluster') // description appears under the title
            .infinitePagination(true) // load pages as the user scrolls
            .fields([
                nga.field('dataset_id').label('dataset_id').map(short_uuid)
            ])
            .listActions(['show']);

        node.showView() // a showView displays one entry in full page - allows to display more data than in a a list
            .fields([
                nga.field('uuid').label('uuid').map(short_uuid), // The default displayed name is the camelCase field name. label() overrides id
                nga.field('host')
            ]);

        volume.showView() // a showView displays one entry in full page - allows to display more data than in a a list
            .fields([
                nga.field('dataset_id').label('dataset_id').map(short_uuid),
                nga.field('deleted', 'boolean'),
                nga.field('maximum_size')
            ]);

        configuration.showView() // a showView displays one entry in full page - allows to display more data than in a a list
            .fields([
                nga.field('dataset_id').label('dataset_id').map(short_uuid),
                nga.field('deleted', 'boolean'),
                nga.field('maximum_size')
            ]);


        state.showView() // a showView displays one entry in full page - allows to display more data than in a a list
            .fields([
                nga.field('dataset_id').label('dataset_id').map(short_uuid)
            ]);


        volume.creationView()
            .fields([
                nga.field('primary', 'reference') // ReferenceMany translates to a select multiple
                    .label('Node')
                    .targetEntity(node)
                    .targetField(nga.field('host')),
                nga.field('size').label('Maximum Size'),
                nga.field('meta').label('Metadata')
            ]);

        volume.editionView()
            .fields([
                nga.field('primary', 'reference') // ReferenceMany translates to a select multiple
                    .label('Node')
                    .targetEntity(node)
                    .targetField(nga.field('host'))
            ]);

        // customize header
        var customHeaderTemplate =
        '<div class="navbar-header">' +
            '<a class="navbar-brand" href="#" ng-click="appController.displayHome()">' + 
                //'<img src="images/clusterhq.png" />' +
                '<img src="images/logo.png" />' +
            '</a>' +
            '<div class="experiment">Experimental GUI</div>'
        '</div>';
        admin.header(customHeaderTemplate);

        // customize menu
        admin.menu(nga.menu()
            .addChild(
                nga.menu()
                .title('Dashboard')
                .link('dashboard')
                .icon('')
            )
            .addChild(
                nga.menu(node)
                .title('Nodes')
                .icon('')
            )
            .addChild(
                nga.menu(volume)
                .title('Datasets')
                .icon('')
            )/*
            .addChild(
                nga.menu()
                .title('Debug')
                .icon('')
                .addChild(
                    nga.menu(configuration)
                    .title('Configuration')
                    .icon('')
                )
                .addChild(
                    nga.menu(state)
                    .title('State')
                    .icon('')
                ) 
            )*/
        );

        nga.configure(admin);
    }]);

}());
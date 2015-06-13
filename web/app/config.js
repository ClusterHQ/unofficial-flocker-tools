/*global angular*/
(function () {
    "use strict";

    var DEBUG = true;
    var BASE_URL = 'https://test.labs.clusterhq.com:4523/v1'

    var app = angular.module('myApp', ['ng-admin']);

    app.config(['NgAdminConfigurationProvider', 'RestangularProvider', function (NgAdminConfigurationProvider, RestangularProvider) {
        var nga = NgAdminConfigurationProvider;

        function truncate(value) {
            if (!value) {
                return '';
            }

            return value.length > 50 ? value.substr(0, 50) + '...' : value;
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
            .baseApiUrl(BASE_URL + '/state/nodes')
            //.identifier(nga.field('id'))

        // set the application entities
        admin
            .addEntity(node)

        // customize entities and views

        node.dashboardView() // customize the dashboard panel for this entity
            .name('nodes')
            .title('Your nodes')
            .order(1) // display the post panel first in the dashboard
            .perPage(5) // limit the panel to the 5 latest posts
            //.fields([nga.field('title').isDetailLink(true).map(truncate)]); // fields() called with arguments add fields to the view

        node.listView()
            .title('All nodes') // default title is "[Entity_name] list"
            .description('Show the nodes in your cluster') // description appears under the title
            .infinitePagination(true) // load pages as the user scrolls
            .fields([
                /*
                nga.field('id').label('id'), // The default displayed name is the camelCase field name. label() overrides id
                nga.field('title'), // the default list field type is "string", and displays as a string
                nga.field('published_at', 'date'),  // Date field type allows date formatting
                nga.field('average_note', 'float'), // Float type also displays decimal digits
                nga.field('views', 'number'),
                nga.field('tags', 'reference_many') // a Reference is a particular type of field that references another entity
                    .targetEntity(tag) // the tag entity is defined later in this file
                    .targetField(nga.field('name')) // the field to be displayed in this list
                */
            ])
            .listActions(['show', 'edit', 'delete']);

        node.creationView()
            .fields([
                /*
                nga.field('title') // the default edit field type is "string", and displays as a text input
                    .attributes({ placeholder: 'the post title' }) // you can add custom attributes, too
                    .validation({ required: true, minlength: 3, maxlength: 100 }), // add validation rules for fields
                nga.field('teaser', 'text'), // text field type translates to a textarea
                nga.field('body', 'wysiwyg'), // overriding the type allows rich text editing for the body
                nga.field('published_at', 'date') // Date field type translates to a datepicker
                */
            ]);

        var subCategories = [
            { category: 'tech', label: 'Computers', value: 'computers' },
            { category: 'tech', label: 'Gadgets', value: 'gadgets' },
            { category: 'lifestyle', label: 'Travel', value: 'travel' },
            { category: 'lifestyle', label: 'Fitness', value: 'fitness' }
        ];

        node.editionView()
            .title('Edit node "{{ entry.values.title }}"') // title() accepts a template string, which has access to the entry
            .actions(['list', 'show', 'delete']) // choose which buttons appear in the top action bar. Show is disabled by default
            .fields([
                /*
                post.creationView().fields(), // fields() without arguments returns the list of fields. That way you can reuse fields from another view to avoid repetition
                nga.field('category', 'choice') // a choice field is rendered as a dropdown in the edition view
                    .choices([ // List the choice as object literals
                        { label: 'Tech', value: 'tech' },
                        { label: 'Lifestyle', value: 'lifestyle' }
                    ]),
                nga.field('subcategory', 'choice')
                    .choices(function(entry) { // choices also accepts a function to return a list of choices based on the current entry
                        return subCategories.filter(function (c) {
                            return c.category === entry.values.category
                        });
                    }),
                nga.field('tags', 'reference_many') // ReferenceMany translates to a select multiple
                    .targetEntity(tag)
                    .targetField(nga.field('name'))
                    .cssClasses('col-sm-4'), // customize look and feel through CSS classes
                nga.field('pictures', 'json'),
                nga.field('views', 'number')
                    .cssClasses('col-sm-4'),
                nga.field('average_note', 'float')
                    .cssClasses('col-sm-4'),
                nga.field('comments', 'referenced_list') // display list of related comments
                    .targetEntity(comment)
                    .targetReferenceField('post_id')
                    .targetFields([
                        nga.field('created_at').label('Posted'),
                        nga.field('body').label('Comment')
                    ])
                    .sortField('created_at')
                    .sortDir('DESC'),
                nga.field('', 'template').label('')
                    .template('<span class="pull-right"><ma-filtered-list-button entity-name="comments" filter="{ post_id: entry.values.id }" size="sm"></ma-filtered-list-button></span>')
                */
            ]);

        node.showView() // a showView displays one entry in full page - allows to display more data than in a a list
            .fields([
                /*
                nga.field('id'),
                post.editionView().fields(), // reuse fields from another view in another order
                nga.field('custom_action', 'template')
                    .label('')
                    .template('<send-email post="entry"></send-email>')
                */
            ]);


        // customize header
        var customHeaderTemplate =
        '<div class="navbar-header">' +
            '<a class="navbar-brand" href="#" ng-click="appController.displayHome()">Flocker GUI</a>' +
        '</div>';
        admin.header(customHeaderTemplate);

        // customize menu
        admin.menu(nga.menu()
            .addChild(nga.menu(node).icon('<span class="glyphicon glyphicon-file"></span>')) // customize the entity menu icon
            .addChild(nga.menu().title('Other')
                .addChild(nga.menu().title('Stats').icon('').link('/stats'))
            )
        );

        nga.configure(admin);
    }]);

}());
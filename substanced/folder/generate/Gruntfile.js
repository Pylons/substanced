
/* jshint node: true */
'use strict';

module.exports = function(grunt) {

    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
        sprite: {
            'options': {
                banner: '/*! substanced.folder generated resource */\n',
            },
            'default': {
                src: 'node_modules/free-file-icons/48px/*.png',
                destImg: '../static/css/images/mimetype-icons.png',
                destCSS: '../static/css/mimetype-icons.css',
                cssOpts: {
                    cssClass: function (item) {
                      return '.mimetype-icon-' + item.name;
                    },
                },
            },
        },
        usebanner: {
            'default': {
                options: {
                    banner: '/*\n' +
                            ' * Resource generated automatically by substanced.folder.\n' +
                            ' * DO NOT EDIT! Regenerate with:\n' +
                            ' *\n' +
                            ' * $ cd substanced/folder/generate; npm install\n' +
                            ' */\n',
                },
                files: {
                    src: '<%= sprite.default.destCSS %>',
                },
            },
        },
    });

    require('load-grunt-tasks')(grunt);

    grunt.registerTask('install', ['sprite', 'usebanner']);

    grunt.registerTask('default', 'install');

};

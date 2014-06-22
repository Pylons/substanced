
/* jshint node: true */
'use strict';

module.exports = function(grunt) {

    grunt.initConfig({
        pkg: grunt.file.readJSON('package.json'),
        sprite: {
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
    });

    // Load the task plugins.
    require('matchdep').filterDev(['grunt-*', '!grunt-cli']).forEach(grunt.loadNpmTasks);

    grunt.registerTask('install', ['sprite']);

    grunt.registerTask('default', 'install');

};

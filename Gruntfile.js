// TODO: also do mkdir as in sdidev
var collect = require('grunt-collection-helper');

module.exports = function(grunt) {

  // Project configuration.
  grunt.initConfig({
    pkg: grunt.file.readJSON('package.json'),
    concat: {
      options: {
        banner: '/*! Built by <%= pkg.name %> version <%= pkg.version %> */\n'
      },
      js: {
        files: {
          'src/substanced/substanced/sdi/static/dist/slickgrid.upstream.js':
            collect.select('slickgrid.upstream.js'),
          'src/substanced/substanced/sdi/static/dist/jquery.js':
            collect.select('jquery.js'),
          'src/substanced/substanced/sdi/static/dist/bootstrap.js':
            collect.select('bootstrap.js')
        }
      },
      css: {
        files: {
          'src/substanced/substanced/sdi/static/dist/slick.grid.upstream.css':
            collect.select('slick.grid.upstream.css')
        }
      }
    },
    uglify: {
      options: {
        banner: '<%= concat.options.banner %>'
      },
      js: {
        files: {
          'src/substanced/substanced/sdi/static/dist/slickgrid.upstream.js':
            collect.select('slickgrid.upstream.js'),
          'src/substanced/substanced/sdi/static/dist/jquery.js':
            collect.select('jquery.js'),
          'src/substanced/substanced/sdi/static/dist/bootstrap.js':
            collect.select('bootstrap.js')

        }
      }
    },
    less: {
      'default': {
        options: {
          paths: ['src/substanced/substanced/sdi/static/css']
        },
        files: {
          'src/substanced/substanced/sdi/static/dist/sdi_bootstrap.css':
            collect.select('sdi_bootstrap.css')
        }
      },
      minify: {
        options: {
          paths: ['src/substanced/substanced/sdi/static/css'],
          yuicompress: true
        },
        files: {
          'src/substanced/substanced/sdi/static/dist/sdi_bootstrap.css':
            collect.select('sdi_bootstrap.css')
        }
      }
    },
    watch: {
      options: {
        debounceDelay: 250
      },
      'default': {
        files: [].concat(
          collect.select('slickgrid.upstream.js'),
          collect.select('jquery.js'),
          collect.select('bootstrap.js'),
          collect.select('slick.grid.upstream.css'),
          collect.select('sdi_bootstrap.css'),
          [
            collect.bower('bootstrap').path('less/bootstrap.less'),
            collect.bower('bootstrap').path('less/responsive.less')
          ]
        ),
        tasks: ['concat:js', 'concat:css', 'less:default']
      },
      minify: {
        files: [].concat(
          collect.select('slickgrid.upstream.js'),
          collect.select('jquery.js'),
          collect.select('bootstrap.js'),
          collect.select('slick.grid.upstream.css'),
          collect.select('sdi_bootstrap.css'), [
            collect.bower('bootstrap').path('less/bootstrap.less'),
            collect.bower('bootstrap').path('less/responsive.less')
          ]
        ),
        tasks: ['uglify:js', 'concat:css', 'less:minify']
      }
    }
  });

  // Load the task plugins.
  grunt.loadNpmTasks('grunt-contrib-uglify');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-watch');
  grunt.loadNpmTasks('grunt-contrib-less');

  // Default task(s).
  grunt.registerTask('default', ['concat:js', 'concat:css', 'less:default']);
  grunt.registerTask('minify', ['uglify:js', 'concat:css', 'less:minify']);

  grunt.registerTask('watch-default', ['watch:default']);
  grunt.registerTask('watch-minify', ['watch:minify']);

};

.PHONY: watch minify

minify: node_modules bower_components
	@node_modules/.bin/grunt minify

watch: node_modules bower_components
	@node_modules/.bin/grunt default
	@node_modules/.bin/grunt watch

node_modules:
	@npm install .

bower_components:
	@node_modules/.bin/bower install

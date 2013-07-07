.PHONY: watch minify

watch: node_modules bower_components
	@node_modules/.bin/grunt watch

minify: node_modules bower_components
	@node_modules/.bin/grunt minify

node_modules:
	@npm install .

bower_components:
	@node_modules/.bin/bower install

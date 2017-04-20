# microplugin.js
[![NPM version](https://badge.fury.io/js/microplugin.png)](http://badge.fury.io/js/microplugin)
[![Build Status](https://travis-ci.org/brianreavis/microplugin.js.png?branch=master)](https://travis-ci.org/brianreavis/microplugin.js)

*Keep code modularized & extensible.* MicroPlugin is a lightweight drop-in plugin architecture for your JavaScript library. Plugins can [declare dependencies](#dependencies) to other plugins and can be [initialized with options](#loading-plugins) (in a variety of formats). It [AMD](http://en.wikipedia.org/wiki/Asynchronous_module_definition)-compatible and it works identically in Node.js and in a browser.

```sh
$ npm install microplugin
$ bower install microplugin
```

## Integration

Using the provided mixin, extend your function with the [API](#mixin-methods) for declaring and loading plugins:

```js
var TextEditor = function(options) {
	this.initializePlugins(options.plugins);
};

MicroPlugin.mixin(TextEditor);
```

That's it for integration! Now you can selectively load the plugins on an instance-by-instance basis.

```js
var editor = new TextEditor({
	plugins: ['links','images']
});
```

### Loading Plugins

The [`initializePlugins()`](#prototypeinitializepluginsplugins) method sets up the plugin system and loads a list of plugins (with options). It accepts the list in three styles, depending on your preference.

#### List (no options)
```js
["plugin_a","plugin_b","plugin_c"]
```

#### List (with options)
```js
[
	{name: "plugin_a", options: { /* ... */ }},
	{name: "plugin_b", options: { /* ... */ }},
	{name: "plugin_c", options: { /* ... */ }}
]
```

#### Hash (with options)
```js
{
	"plugin_a": { /* ... */ },
	"plugin_b": { /* ... */ },
	"plugin_c": { /* ... */ }
}
```

## Plugin Design

Plugins aren't extravagant—they are barebones by design. A plugin is simply a function that gets called when an instance of your object is being constructed. Within that function, you can manually override methods, set up event listeners, etc. The `this` context will be the instance of your object.

### Defining Plugins

```js
MyLibrary.define("math", function(options) {
	// You can return values which will be available to other plugins
	// when they load the plugin via "require()". Explained more in
	// the next section.
	return {
		random : Math.random,
		sqrt   : Math.sqrt,
		sin2   : function(t) { return Math.pow(Math.sin(t), 2); },
		cos2   : function(t) { return Math.pow(Math.sin(t), 2); }
	};
});
```

#### Dependencies

Plugins can declare dependencies to other plugins (and use any exports they provide) through the [`require`](#prototyperequirename) function.

```js
MyLibrary.define("calculations", function(options) {
	var math    = this.require("math");
	var theta   = math.random();
	var success = math.sqrt(math.sin2(theta) + math.cos2(theta)) === 1;

	alert("Does the law of sines work? " + success);
});
```

## API Reference

#### MicroPlugin.mixin(fn)
Sets up all methods on the function and its prototype for defining and loading plugins.

### Mixin Methods

#### define(name, fn)
Declares a new plugin with the specified name.

#### [prototype].require(name)
Loads a plugin as a dependency and returns whatever it exports (if anything).

#### [prototype].initializePlugins(plugins)
Initializes the plugin system and loads a list of plugins with the provided options. The "plugins" argument can be in a [variety of formats](#loading-plugins).

## License

Copyright &copy; 2013 [Brian Reavis](http://twitter.com/brianreavis) & [Contributors](https://github.com/brianreavis/microplugin.js/graphs/contributors)

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

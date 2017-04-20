# sifter.js
[![NPM version](http://img.shields.io/npm/v/sifter.svg?style=flat)](https://www.npmjs.org/package/sifter)
[![Installs](http://img.shields.io/npm/dm/sifter.svg?style=flat)](https://www.npmjs.org/package/sifter)
[![Build Status](https://travis-ci.org/brianreavis/sifter.js.svg)](https://travis-ci.org/brianreavis/sifter.js)
[![Coverage Status](http://img.shields.io/coveralls/brianreavis/sifter.js/master.svg?style=flat)](https://coveralls.io/r/brianreavis/sifter.js)

Sifter is a client and server-side library (via [UMD](https://github.com/umdjs/umd)) for textually searching arrays and hashes of objects by property – or multiple properties. It's designed specifically for autocomplete. The process is three-step: *score*, *filter*, *sort*.

* **Supports díåcritîçs.**<br>For example, if searching for "montana" and an item in the set has a value of "montaña", it will still be matched. Sorting will also play nicely with diacritics.
* **Smart scoring.**<br>Items are scored / sorted intelligently depending on where a match is found in the string (how close to the beginning) and what percentage of the string matches.
* **Multi-field sorting.**<br>When scores aren't enough to go by – like when getting results for an empty query – it can sort by one or more fields. For example, sort by a person's first name and last name without actually merging the properties to a single string.
* **Nested properties.**<br>Allows to search and sort on nested properties so you can perform search on complex objects without flattening them simply by using dot-notation to reference fields (ie. `nested.property`).

```sh
$ npm install sifter # node.js
$ bower install sifter # browser
```

## Usage

```js
var sifter = new Sifter([
	{title: 'Annapurna I', location: 'Nepal', continent: 'Asia'},
	{title: 'Annapurna II', location: 'Nepal', continent: 'Asia'},
	{title: 'Annapurna III', location: 'Nepal', continent: 'Asia'},
	{title: 'Eiger', location: 'Switzerland', continent: 'Europe'},
	{title: 'Everest', location: 'Nepal', continent: 'Asia'},
	{title: 'Gannett', location: 'Wyoming', continent: 'North America'},
	{title: 'Denali', location: 'Alaska', continent: 'North America'}
]);

var result = sifter.search('anna', {
	fields: ['title', 'location', 'continent'],
	sort: [{field: 'title', direction: 'asc'}],
	limit: 3
});
```

Seaching will provide back meta information and an "items" array that contains objects with the index (or key, if searching a hash) and a score that represents how good of a match the item was. Items that did not match will not be returned.

```
{"score": 0.2878787878787879, "id": 0},
{"score": 0.27777777777777773, "id": 1},
{"score": 0.2692307692307692, "id": 2}
```

Items are sorted by best-match, primarily. If two or more items have the same score (which will be the case when searching with an empty string), it will resort to the fields listed in the "sort" option.

The full result comes back in the format of:

```js
{
	"options": {
		"fields": ["title", "location", "continent"],
		"sort": [
			{"field": "title", "direction": "asc"}
		],
		"limit": 3
	},
	"query": "anna",
	"tokens": [{
		"string": "anna",
		"regex": /[aÀÁÂÃÄÅàáâãäå][nÑñ][nÑñ][aÀÁÂÃÄÅàáâãäå]/
	}],
	"total": 3,
	"items": [
		{"score": 0.2878787878787879, "id": 0},
		{"score": 0.27777777777777773, "id": 1},
		{"score": 0.2692307692307692,"id": 2}
	]
}
```

### API

#### #.search(query, options)

Performs a search for `query` with the provided `options`.

<table width="100%">
	<tr>
		<th align="left">Option</th>
		<th align="left">Type</th>
		<th align="left" width="100%">Description</th>
	</tr>
	<tr>
		<td valign="top"><code>fields</code></td>
		<td valign="top">array</td>
		<td valign="top">An array of property names to be searched.</td>
	</tr>
	<tr>
		<td valign="top"><code>limit</code></td>
		<td valign="top">integer</td>
		<td valign="top">The maximum number of results to return.</td>
	</tr>
	<tr>
		<td valign="top"><code>sort</code></td>
		<td valign="top">array</td>
		<td valign="top">An array of fields to sort by. Each item should be an object containing at least a <code>"field"</code> property. Optionally, <code>direction</code> can be set to <code>"asc"</code> or <code>"desc"</code>. The order of the array defines the sort precedence.<br><br>Unless present, a special <code>"$score"</code> property will be automatically added to the beginning of the sort list. This will make results sorted primarily by match quality (descending).</td>
	</tr>
	<tr>
		<td valign="top"><code>sort_empty</code></td>
		<td valign="top">array</td>
		<td valign="top">Optional. Defaults to "sort" setting. If provided, these sort settings are used when no query is present.</td>
	</tr>
	<tr>
		<td valign="top"><code>filter</code></td>
		<td valign="top">boolean</td>
		<td valign="top">If <code>false</code>, items with a score of zero will <em>not</em> be filtered out of the result-set.</td>
	</tr>
	<tr>
		<td valign="top"><code>conjunction</code></td>
		<td valign="top">string</td>
		<td valign="top">Determines how multiple search terms are joined (<code>"and"</code> or <code>"or"</code>, defaults to <code>"or"</code>).</td>
	</tr>
	<tr>
		<td valign="top"><code>nesting</code></td>
		<td valign="top">boolean</td>
		<td valign="top">If <code>true</code>, nested fields will be available for search and sort using dot-notation to reference them (e.g. <code>nested.property</code>)<br><em>Warning: can reduce performance</em></td>
	</tr>
</table>

## CLI

![CLI](http://i.imgur.com/fSQBnWZ.png)

Sifter comes with a command line interface that's useful for testing on datasets. It accepts JSON and CSV data, either from a file or from stdin (unix pipes). If using CSV data, the first line of the file must be a header row.
```sh
$ npm install -g sifter
```

```sh
$ cat file.csv | sifter --query="ant" --fields=title
$ sifter --query="ant" --fields=title --file=file.csv
```

## Contributing

Install the dependencies that are required to build and test:

```sh
$ npm install
```

First build a copy with `make` then run the test suite with `make test`.

When issuing a pull request, please exclude "sifter.js" and "sifter.min.js" in the project root.

## License

Copyright &copy; 2013–2015 [Brian Reavis](http://twitter.com/brianreavis) & [Contributors](https://github.com/brianreavis/sifter.js/graphs/contributors)

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

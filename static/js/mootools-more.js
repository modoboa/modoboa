//MooTools More, <http://mootools.net/more>. Copyright (c) 2006-2009 Aaron Newton <http://clientcide.com/>, Valerio Proietti <http://mad4milk.net> & the MooTools team <http://mootools.net/developers>, MIT Style License.

/*
---

script: More.js

description: MooTools More

license: MIT-style license

authors:
- Guillermo Rauch
- Thomas Aylott
- Scott Kyle

requires:
- core:1.2.4/MooTools

provides: [MooTools.More]

...
*/

MooTools.More = {
	'version': '1.2.4.2',
	'build': 'bd5a93c0913cce25917c48cbdacde568e15e02ef'
};

/*
---

script: Fx.Slide.js

description: Effect to slide an element in and out of view.

license: MIT-style license

authors:
- Valerio Proietti

requires:
- core:1.2.4/Fx Element.Style
- /MooTools.More

provides: [Fx.Slide]

...
*/

Fx.Slide = new Class({

	Extends: Fx,

	options: {
		mode: 'vertical',
		hideOverflow: true
	},

	initialize: function(element, options){
		this.addEvent('complete', function(){
			this.open = (this.wrapper['offset' + this.layout.capitalize()] != 0);
			if (this.open && Browser.Engine.webkit419) this.element.dispose().inject(this.wrapper);
		}, true);
		this.element = this.subject = document.id(element);
		this.parent(options);
		var wrapper = this.element.retrieve('wrapper');
		var styles = this.element.getStyles('margin', 'position', 'overflow');
		if (this.options.hideOverflow) styles = $extend(styles, {overflow: 'hidden'});
		this.wrapper = wrapper || new Element('div', {
			styles: styles
		}).wraps(this.element);
		this.element.store('wrapper', this.wrapper).setStyle('margin', 0);
		this.now = [];
		this.open = true;
	},

	vertical: function(){
		this.margin = 'margin-top';
		this.layout = 'height';
		this.offset = this.element.offsetHeight;
	},

	horizontal: function(){
		this.margin = 'margin-left';
		this.layout = 'width';
		this.offset = this.element.offsetWidth;
	},

	set: function(now){
		this.element.setStyle(this.margin, now[0]);
		this.wrapper.setStyle(this.layout, now[1]);
		return this;
	},

	compute: function(from, to, delta){
		return [0, 1].map(function(i){
			return Fx.compute(from[i], to[i], delta);
		});
	},

	start: function(how, mode){
		if (!this.check(how, mode)) return this;
		this[mode || this.options.mode]();
		var margin = this.element.getStyle(this.margin).toInt();
		var layout = this.wrapper.getStyle(this.layout).toInt();
		var caseIn = [[margin, layout], [0, this.offset]];
		var caseOut = [[margin, layout], [-this.offset, 0]];
		var start;
		switch (how){
			case 'in': start = caseIn; break;
			case 'out': start = caseOut; break;
			case 'toggle': start = (layout == 0) ? caseIn : caseOut;
		}
		return this.parent(start[0], start[1]);
	},

	slideIn: function(mode){
		return this.start('in', mode);
	},

	slideOut: function(mode){
		return this.start('out', mode);
	},

	hide: function(mode){
		this[mode || this.options.mode]();
		this.open = false;
		return this.set([-this.offset, 0]);
	},

	show: function(mode){
		this[mode || this.options.mode]();
		this.open = true;
		return this.set([0, this.offset]);
	},

	toggle: function(mode){
		return this.start('toggle', mode);
	}

});

Element.Properties.slide = {

	set: function(options){
		var slide = this.retrieve('slide');
		if (slide) slide.cancel();
		return this.eliminate('slide').store('slide:options', $extend({link: 'cancel'}, options));
	},

	get: function(options){
		if (options || !this.retrieve('slide')){
			if (options || !this.retrieve('slide:options')) this.set('slide', options);
			this.store('slide', new Fx.Slide(this, this.retrieve('slide:options')));
		}
		return this.retrieve('slide');
	}

};

Element.implement({

	slide: function(how, mode){
		how = how || 'toggle';
		var slide = this.get('slide'), toggle;
		switch (how){
			case 'hide': slide.hide(mode); break;
			case 'show': slide.show(mode); break;
			case 'toggle':
				var flag = this.retrieve('slide:flag', slide.open);
				slide[flag ? 'slideOut' : 'slideIn'](mode);
				this.store('slide:flag', !flag);
				toggle = true;
			break;
			default: slide.start(how, mode);
		}
		if (!toggle) this.eliminate('slide:flag');
		return this;
	}

});


/*
---

script: Tips.js

description: Class for creating nice tips that follow the mouse cursor when hovering an element.

license: MIT-style license

authors:
- Valerio Proietti
- Christoph Pojer

requires:
- core:1.2.4/Options
- core:1.2.4/Events
- core:1.2.4/Element.Event
- core:1.2.4/Element.Style
- core:1.2.4/Element.Dimensions
- /MooTools.More

provides: [Tips]

...
*/

(function(){

var read = function(option, element){
    return (option) ? ($type(option) == 'function' ? option(element) : element.get(option)) : '';
};

this.Tips = new Class({

    Implements: [Events, Options],

    options: {
        /*
        onAttach: $empty(element),
        onDetach: $empty(element),
        */
        onShow: function(){
            this.tip.setStyle('display', 'block');
        },
        onHide: function(){
            this.tip.setStyle('display', 'none');
        },
        title: 'title',
        text: function(element){
            return element.get('rel') || element.get('href');
        },
        showDelay: 100,
        hideDelay: 100,
        className: 'tip-wrap',
        offset: {x: 16, y: 16},
        fixed: false
    },

    initialize: function(){
        var params = Array.link(arguments, {options: Object.type, elements: $defined});
        this.setOptions(params.options);
        document.id(this);
        
        if (params.elements) this.attach(params.elements);
    },

    toElement: function(){
        if (this.tip) return this.tip;
        
        this.container = new Element('div', {'class': 'tip'});
        return this.tip = new Element('div', {
            'class': this.options.className,
            styles: {
                position: 'absolute',
                top: 0,
                left: 0,
                visibility: 'hidden',
                display: 'none'
            }
        }).adopt(
            new Element('div', {'class': 'tip-top'}),
            this.container,
            new Element('div', {'class': 'tip-bottom'})
        ).inject(document.body);
    },
    
    attach: function(elements){
        $$(elements).each(function(element){
            var title = read(this.options.title, element),
                text = read(this.options.text, element);
            
            element.erase('title').store('tip:native', title).retrieve('tip:title', title);
            element.retrieve('tip:text', text);
            this.fireEvent('attach', [element]);
            
            var events = ['enter', 'leave'];
            if (!this.options.fixed) events.push('move');

            events.each(function(value){
                var event = element.retrieve('tip:' + value);
                if (!event) event = this['element' + value.capitalize()].bindWithEvent(this, element);
                element.store('tip:' + value, event).addEvent('mouse' + value, event);
            }, this);
            
            element.addEvent('mouseout', this.hide.bind(this, element)); // firefox doesn't handle mouseleave correct
            
        }, this);
        
        return this;
    },
    
    detach: function(elements){
        $$(elements).each(function(element){
            ['enter', 'leave', 'move'].each(function(value){
                element.removeEvent('mouse' + value, element.retrieve('tip:' + value)).eliminate('tip:' + value);
            });
            
            this.fireEvent('detach', [element]);
            
            if (this.options.title == 'title'){ // This is necessary to check if we can revert the title
                var original = element.retrieve('tip:native');
                if (original) element.set('title', original);
            }
        }, this);
        
        return this;
    },
    
    elementEnter: function(event, element){
        this.container.empty();
        
        ['title', 'text'].each(function(value){
            var content = element.retrieve('tip:' + value);
            if (content) this.fill(new Element('div', {'class': 'tip-' + value}).inject(this.container), content);
        }, this);
        
        $clear(this.timer);
        this.timer = this.show.delay(this.options.showDelay, this, [element, event]);
    },
    
    elementLeave: function(event, element){
        this.tip.setStyle('visibility', 'hidden');
        $clear(this.timer);
        this.timer = this.hide.delay(this.options.hideDelay, this, element);
        this.fireForParent(event, element);
    },
    
    fireForParent: function(event, element){
        var element = $(element);
        if (!element) return;
        parentNode = element.getParent();
        if (parentNode == document.body) return;
        if (parentNode.retrieve('tip:enter')) parentNode.fireEvent('mouseenter', event);
        else this.fireForParent(event, parentNode);
    },
    
    elementMove: function(event, element) {
        this.position(event);
    },

    position: function(event){
        if (this.tip.getStyle('display') != 'block') return;
        var size = window.getSize(), scroll = window.getScroll(),
            tip = {x: this.tip.offsetWidth, y: this.tip.offsetHeight},
            props = {x: 'left', y: 'top'},
            obj = {};
        
        for (var z in props){
            obj[props[z]] = event.page[z] + this.options.offset[z];
            if ((obj[props[z]] + tip[z] - scroll[z]) > size[z]) obj[props[z]] = event.page[z] - this.options.offset[z] - tip[z];
        }
        
        this.tip.setStyles(obj);
        this.tip.setStyle('visibility', 'visible');
    },
    
    fill: function(element, contents){
        if(typeof contents == 'string') element.set('html', contents);
        else element.adopt(contents);
    },
    
    show: function(element, event) {
        this.fireEvent('show', [this.tip, element]);
        this.position((this.options.fixed) ? {page: element.getPosition()} : event);
    },
    
    hide: function(element){
        this.fireEvent('hide', [this.tip, element]);
    }
    
});

})();
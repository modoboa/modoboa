/*
---
description:     ProgressBar

authors:
  - David Walsh (http://davidwalsh.name)

license:
  - MIT-style license

requires:
  core/1.2.1:   '*'
  more/1.2.1:   'Fx.*'

provides:
  - ProgressBar
...
*/
var ProgressBar=new Class({Implements:[Events,Options],options:{container:document.body,boxID:"progress-bar-box-id",percentageID:"progress-bar-percentage-id",displayID:"progress-bar-display-id",startPercentage:0,displayText:false,speed:10,step:1,allowMore:false,onComplete:$empty,onChange:$empty},initialize:function(a){this.setOptions(a);this.options.container=document.id(this.options.container);this.createElements();},createElements:function(){var b=new Element("div",{id:this.options.boxID});var a=new Element("div",{id:this.options.percentageID,style:"width:0px;"});a.inject(b);b.inject(this.options.container);if(this.options.displayText){var c=new Element("div",{id:this.options.displayID});c.inject(this.options.container);}this.set(this.options.startPercentage);},calculate:function(a){return(document.id(this.options.boxID).getStyle("width").replace("px","")*(a/100)).toInt();},animate:function(b){var c=false;var a=this;if(!a.options.allowMore&&b>100){b=100;}a.to=b.toInt();document.id(a.options.percentageID).set("morph",{duration:this.options.speed,link:"cancel",onComplete:function(){a.fireEvent("change",[a.to]);if(b>=100){a.fireEvent("complete",[a.to]);}}}).morph({width:a.calculate(b)});if(a.options.displayText){document.id(a.options.displayID).set("text",a.to+"%");}},set:function(a){this.animate(a);},step:function(){this.set(this.to+this.options.step);}});
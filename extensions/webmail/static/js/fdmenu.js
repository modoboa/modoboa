/*
 * Simple dropdown menu plugin used for folders manipulation.
 *
 */
var FdMenu = new Class({
    Implements: [Options],

    options: {
      media_url: "",
      modify_url: "",
      delete_url: ""
    },

    add_entry: function(name, label, pic, url, onclick) {
      var item = new Element("li");
      var picpath = this.options.media_url + "pics/" + pic;

      this[name] = new Element("a")
        .set("html", "<img src='" + picpath + "' /> " + label)
        .addEvent("click", onclick)
        .inject(item);
      item.inject(this.list);
    },

    initialize: function(options) {
      this.setOptions(options);

      this.container = new Element("div", {"id" : "fdmenu"})
        .addClass("fdmenu");
      this.list = new Element("ul");

      this.add_entry("modbutton", gettext("Edit folder"),
        "edit.png", this.options.modify_url, function(evt) {
          evt.stop();
          SqueezeBox.initialize({
            size: {x: 350, y: 400},
            handler: 'iframe'
          });
          SqueezeBox.open(this.get("href"));
        });
      this.add_entry("delbutton", gettext("Delete folder"), "remove.png",
                    this.options.delete_url, function(evt) {
                      evt.stop();
                      if (!confirm(gettext("Delete folder?"))) {
                        return;
                      }
                      new Request.JSON({
                        url: this.get("href"),
                        method: "GET",
                        onSuccess: function(resp) {
                          if (resp.status == "ok") {
                            infobox.info(gettext("Folder deleted."));
                            var id = current_anchor.update.delay(500, current_anchor, 1);
                          } else {
                            infobox.error(gettext("Failed to delete folder"));
                            infobox.hide(2);
                          }
                        }
                      }).send();
                    });
      this.list.inject(this.container);
      this.shown = false;

      $(document.body).addEvent("click", function() {
        if (this.shown) {
          this.hide();
        }
      }.bind(this));
      //this.fx = new Fx.Slide(this.container);
    },

    show: function(origin, folder) {
      var position = origin.getPosition();

      this.container.setStyles({
          position: "absolute",
          top: position.y + 5,
          left: position.x + 5,
          display: "block"
      });
      this.container.inject(document.body);
      this.shown = true;
      this.modbutton.set("href", this.options.modify_url + "?name=" + folder);
    },

    hide: function() {
      this.container.setStyles({
        display: "none"
      });
      this.container.dispose();
      this.shown = false;
    },

    toggle: function(origin, folder) {
      return (!this.shown) ? this.show(origin, folder) : this.hide();
    }
});